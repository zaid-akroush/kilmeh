"""Track B grader for arabic-file-io.

The grader writes a fresh input directory (Arabic data drawn per run from the pools below, so
the expected values are not in the image at agent time), runs the agent's /app/ingest.py on it
as uid 65534 in its own session, then reads the output files as bytes and decides. Expected
values are computed here from the generated data; nothing the agent writes can decide the
result. Output is one boolean per check as JSON; exit 0 only if all pass. Run with
`python3 -B -I -S` (see test.sh).

Fails closed: before running anything, the tests directory and everything in it must be owned
by the grading user with no group or other access (exit 2). Output files are read without
following links (a link out of the output directory scores 0). When root, processes of uid 65534
are killed before and after the run (agent daemons that outlive it).

The fixed bug classes behind the checks: a BOM leaking into the first CSV header, Windows-1256
bytes read with the wrong codec, JSON written with ensure_ascii escapes, output file names
losing their Arabic characters. File names are compared as raw UTF-8 bytes.
"""

import csv
import io
import json
import os
import random
import shutil
import signal
import stat
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

APP = os.environ.get("KILMEH_APP", "/app")
HERE = os.path.dirname(os.path.abspath(__file__))
NOBODY = 65534
MAX_BYTES = 1_000_000
MAX_FILES = 50
TIMEOUT = 30
BOM = b"\xef\xbb\xbf"
RNG = random.SystemRandom()

# All names are encodable in Windows-1256 (checked in make_data).
PRODUCTS = [
    "قهوة", "شاي أخضر", "زيت زيتون", "تمر", "حليب", "جبنة بيضاء",
    "خبز عربي", "عسل", "لبن", "زعتر", "أرز", "إبريق",
]  # fmt: skip
CITIES = ["عمان", "إربد", "الزرقاء", "العقبة", "مأدبا", "جرش", "السلط"]
TITLES = ["متجر الحارة", "بقالة الحي", "سوق الخضار"]
DOC_FIRST = ["تقرير", "ملخص", "فاتورة", "قائمة", "جرد", "طلبات"]
DOC_SECOND = ["المبيعات", "الأسبوع", "الشهر", "المخزون"]
SENTENCES = ["ملخص المبيعات لهذا الأسبوع", "وصلت الطلبية الجديدة اليوم", "نفد المخزون من القهوة"]

CHECKS = [
    "runs_ok",
    "csv_header_clean",
    "csv_utf8_values",
    "legacy_cp1256_decoded",
    "json_values_exact",
    "json_not_escaped",
    "no_bom_in_outputs",
    "doc_filenames_arabic",
    "doc_contents_exact",
]
DETAIL = {
    "runs_ok": "ingest.py exits 0 within the time limit",
    "csv_header_clean": "products.csv header names carry no BOM",
    "csv_utf8_values": "products.csv values read as UTF-8",
    "legacy_cp1256_decoded": "legacy.csv decoded as Windows-1256",
    "json_values_exact": "summary.json has the title, products, legacy and docs",
    "json_not_escaped": "summary.json holds Arabic as UTF-8, not \\u escapes",
    "no_bom_in_outputs": "no output file starts with a BOM",
    "doc_filenames_arabic": "doc summary file names keep their Arabic characters",
    "doc_contents_exact": "doc summary files hold the first line of each doc",
}


def log_checks(report: dict[str, bool], detail: dict[str, str], reason: str | None) -> None:
    """One `PASS key: detail` / `FAIL key: detail` line per check on stderr, in report order
    (the RTL graders' format). Details are fixed text: no input or expected value is printed."""
    for key, ok in report.items():
        why = detail[key] if ok else reason or f"expected {detail[key]}"
        print(f"{'PASS' if ok else 'FAIL'} {key}: {why}", file=sys.stderr)


def unlocked_path(root: str) -> str | None:
    """The first path under `root` (itself included) that another user could reach: not owned
    by this process's user, or any group/other permission bit set. None when locked."""
    me = os.geteuid()
    for dirpath, dirnames, filenames in os.walk(root):
        for path in [dirpath, *(os.path.join(dirpath, n) for n in dirnames + filenames)]:
            st = os.lstat(path)
            if st.st_uid != me or st.st_mode & 0o077:
                return f"{path} (owner {st.st_uid}, mode {oct(st.st_mode & 0o7777)})"
    return None


def sweep() -> None:
    """kill(-1) as uid 65534 signals every process of that uid, daemons included. Root only."""
    if os.geteuid() != 0:
        return
    for _ in range(3):
        subprocess.run(
            [sys.executable, "-B", "-I", "-S", "-c", "import os, signal; os.kill(-1, 9)"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd="/",
            env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
            timeout=30,
            user=NOBODY,
            group=NOBODY,
            extra_groups=[],
        )


def csv_text(rows: list[list[str]]) -> str:
    out = io.StringIO(newline="")
    csv.writer(out).writerows(rows)
    return out.getvalue()


def make_data() -> dict:
    """Inputs for this run plus everything the grader expects back."""
    names = RNG.sample(PRODUCTS, 4)
    products = [
        {"id": str(i), "name": n, "city": RNG.choice(CITIES)} for i, n in enumerate(names, 1)
    ]
    legacy = [
        {"id": str(i), "name": n} for i, n in enumerate(RNG.sample(PRODUCTS, 3), RNG.randint(5, 40))
    ]
    stems = set()
    while len(stems) < 3:
        stems.add(f"{RNG.choice(DOC_FIRST)}_{RNG.choice(DOC_SECOND)}")
    docs = {s: RNG.choice(SENTENCES) for s in sorted(stems)}
    return {"title": RNG.choice(TITLES), "products": products, "legacy": legacy, "docs": docs}


def write_inputs(root: str, data: dict) -> None:
    def put(name: str, raw: bytes) -> None:
        with open(os.path.join(root, name), "wb") as f:
            f.write(raw)

    rows = [["id", "name", "city"]] + [list(p.values()) for p in data["products"]]
    put("products.csv", BOM + csv_text(rows).encode("utf-8"))
    rows = [["id", "name"]] + [list(p.values()) for p in data["legacy"]]
    put("legacy.csv", csv_text(rows).encode("windows-1256"))
    config = json.dumps({"title": data["title"]}, ensure_ascii=False, indent=2)
    put("config.json", config.encode("utf-8"))
    os.mkdir(os.path.join(root, "docs"))
    for stem, line in data["docs"].items():
        put(f"docs/{stem}.txt", (line + "\nالسطر الثاني\n").encode("utf-8"))


def _as_nobody() -> dict:
    """Drop to uid 65534 when root. Not root: no drop, process-group kill only."""
    if os.geteuid() != 0:
        return {}
    return {"user": NOBODY, "group": NOBODY, "extra_groups": []}


def run_ingest(in_dir: str, out_dir: str, cwd: str) -> bool:
    """Run the agent's script in its own session; True if it exits 0 in time."""
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LC_ALL": "C.UTF-8", "HOME": cwd}
    proc = subprocess.Popen(
        # EncodingWarning is an error: a text open() with no encoding= fails here, so a solution
        # cannot lean on the locale default (UTF-8 under C.UTF-8, cp1256 or ASCII elsewhere).
        # A truly non-UTF-8 locale is not used: it would also break Arabic file names (fsencoding).
        [
            sys.executable,
            "-B",
            "-X",
            "warn_default_encoding",
            "-W",
            "error::EncodingWarning",
            os.path.join(APP, "ingest.py"),
            in_dir,
            out_dir,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=cwd,
        env=env,
        start_new_session=True,
        **_as_nobody(),
    )
    try:
        ok = proc.wait(timeout=TIMEOUT) == 0
    except subprocess.TimeoutExpired:
        ok = False
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except OSError:
        pass
    proc.wait()
    return ok


def read_regular(path: bytes) -> bytes | None:
    """Bytes of a regular file reached without a symlink, or None (missing, link, FIFO, big)."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return None
    with os.fdopen(fd, "rb") as f:
        st = os.fstat(f.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_BYTES:
            return None
        return f.read()


def read_outputs(out_dir: str) -> tuple[bytes | None, dict[bytes, bytes | None]]:
    """summary.json bytes and {raw file name: bytes} for out/docs/ (names as raw bytes)."""
    root = os.fsencode(out_dir)
    summary = read_regular(os.path.join(root, b"summary.json"))
    docs: dict[bytes, bytes | None] = {}
    docs_dir = os.path.join(root, b"docs")
    try:
        is_real_dir = stat.S_ISDIR(os.lstat(docs_dir).st_mode)
        names = os.listdir(docs_dir)[:MAX_FILES] if is_real_dir else []
    except OSError:
        names = []
    for name in names:
        docs[name] = read_regular(os.path.join(docs_dir, name))
    return summary, docs


def grade(ran: bool, summary: bytes | None, docs: dict[bytes, bytes | None], data: dict) -> dict:
    try:
        parsed = json.loads((summary or b"").decode("utf-8-sig"))
    except ValueError:  # includes UnicodeDecodeError
        parsed = None
    if not isinstance(parsed, dict):
        parsed = {}
    products, legacy = parsed.get("products"), parsed.get("legacy")
    names = [p["name"] for p in data["products"]]
    want_docs = {f"{s}.summary.txt".encode(): s for s in data["docs"]}

    def rows(value) -> list | None:
        ok = isinstance(value, list) and all(isinstance(r, dict) for r in value)
        return value if ok else None

    products, legacy = rows(products), rows(legacy)
    contents_ok = True
    for raw_name, stem in want_docs.items():
        got = docs.get(raw_name)
        want = (data["docs"][stem] + "\n").encode("utf-8")
        contents_ok &= got is not None and got.removeprefix(BOM) == want
    outputs = [b for b in [summary, *docs.values()] if b is not None]
    return {
        "runs_ok": ran,
        "csv_header_clean": products is not None
        and len(products) == len(data["products"])
        and all(list(r) == ["id", "name", "city"] for r in products),
        "csv_utf8_values": products is not None
        and [list(r.values()) for r in products] == [list(p.values()) for p in data["products"]],
        "legacy_cp1256_decoded": legacy == data["legacy"],
        "json_values_exact": parsed.get("title") == data["title"]
        and parsed.get("docs") == list(data["docs"]),
        "json_not_escaped": summary is not None
        and b"\\u" not in summary
        and all(n.encode("utf-8") in summary for n in names),
        "no_bom_in_outputs": summary is not None and not any(b.startswith(BOM) for b in outputs),
        "doc_filenames_arabic": set(docs) == set(want_docs),
        "doc_contents_exact": contents_ok,
    }


def main() -> None:
    reachable = unlocked_path(HERE)
    if reachable is not None:
        print(f"refusing to grade: grader files readable by others: {reachable}", file=sys.stderr)
        sys.exit(2)
    data = make_data()
    work = tempfile.mkdtemp(prefix="kilmeh-io-")
    try:
        in_dir, out_dir = os.path.join(work, "in"), os.path.join(work, "out")
        os.mkdir(in_dir)
        os.mkdir(out_dir)
        write_inputs(in_dir, data)
        for path in (work, in_dir, out_dir):
            os.chmod(path, 0o755)
        for dirpath, _, files in os.walk(in_dir):
            os.chmod(dirpath, 0o755)
            for name in files:
                os.chmod(os.path.join(dirpath, name), 0o644)
        if os.geteuid() == 0:
            os.chown(out_dir, NOBODY, NOBODY)
        sweep()
        ran = run_ingest(in_dir, out_dir, work)
        sweep()
        summary, docs = read_outputs(out_dir)
        report = grade(ran, summary, docs, data)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    log_checks(report, DETAIL, None)
    print(json.dumps(report, indent=1))
    sys.exit(0 if all(report.values()) else 1)


main()
