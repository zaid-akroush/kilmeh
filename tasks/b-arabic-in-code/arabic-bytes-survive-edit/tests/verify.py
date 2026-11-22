"""Track B grader for arabic-bytes-survive-edit. It never runs or imports anything from the app.

The agent edits three files; this script reads their bytes once, up front, and compares them
with the original bytes in tests/golden/ (mounted only at grade time, locked to root by
test.sh). All expected values are computed here from the golden bytes plus the three requested
edits, so nothing the agent writes can decide the result. Output is one boolean per check as
JSON; exit 0 only if all pass. Run with `python3 -B -I -S` (see test.sh).

Fixed edit, so there are no random inputs: a forged answer would have to be the edited files
themselves. Hard-coding is useless too, the golden bytes are not in the image at agent time.

Fails closed: before reading the app, the tests directory and everything in it must be owned by
the grading user with no group or other access (exit 2). The app files must be regular files
reached without a symlink (a link into the grader or elsewhere scores 0). When root, processes
of uid 65534 are killed before and after the read (agent daemons that outlive solve.sh).

Invisible characters are written with chr(); the source stays escape-clean.
"""

import difflib
import json
import os
import stat
import subprocess
import sys

sys.dont_write_bytecode = True

APP = os.environ.get("KILMEH_APP", "/app")
HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN = os.path.join(HERE, "golden")
NOBODY = 65534
MAX_BYTES = 1_000_000

TS, CSV, README = "src/strings.ts", "locale/ar.csv", "README.md"
FILES = [TS, CSV, README]

OLD_VERSION = 'export const VERSION = "2.3.0";'
NEW_VERSION = 'export const VERSION = "2.4.0";'
ANCHOR_KEY = "checkout_title"
ENTRY = '  checkout_subtitle: "راجع طلبك قبل الدفع",'
ROW = "checkout_subtitle,راجع طلبك قبل الدفع"

BIDI = {0x200E, 0x200F, 0x061C, *range(0x202A, 0x202F), *range(0x2066, 0x206A)}
ZW = {0x200C, 0x200D}
KEPT = {0xFDF2, 0x00A0}  # NFKC rewrites both
BIDI_KEYS = ["phone", "embed", "isolates", "alm"]
ZW_KEYS = ["zwnj", "zwj_word", "family"]
MARK_KEYS = ["marks"]
NFD_KEYS = ["nfd"]
KEPT_KEYS = ["allah", "nbsp"]
CHECKS = [
    "version_bumped",
    "entry_inserted",
    "csv_row_appended",
    "untouched_lines_identical",
    "bidi_controls_preserved",
    "zwj_zwnj_preserved",
    "mark_order_preserved",
    "nfd_line_preserved",
    "nfkc_char_kept",
    "no_final_newline_added",
    "crlf_preserved",
    "no_bom",
    "valid_utf8",
    "readme_unchanged",
]
DETAIL = {
    "version_bumped": "VERSION is 2.4.0, once",
    "entry_inserted": "checkout_subtitle entry right after checkout_title",
    "csv_row_appended": "checkout_subtitle row appended to ar.csv",
    "untouched_lines_identical": "no other line changed",
    "bidi_controls_preserved": "bidi controls kept in place",
    "zwj_zwnj_preserved": "ZWJ/ZWNJ kept in place",
    "mark_order_preserved": "combining mark order kept",
    "nfd_line_preserved": "decomposed line not composed",
    "nfkc_char_kept": "ligature and no-break space kept",
    "no_final_newline_added": "strings.ts still has no final newline",
    "crlf_preserved": "ar.csv keeps CRLF, strings.ts keeps LF",
    "no_bom": "no BOM added",
    "valid_utf8": "files are valid UTF-8",
    "readme_unchanged": "README.md byte-identical",
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


def read_app(name: str) -> bytes | None:
    """Bytes of an app file, or None: missing, not a regular file, reached through a symlink,
    or too large."""
    parent = os.path.dirname(os.path.join(APP, name))
    if parent != APP and os.path.islink(parent):
        return None
    try:
        fd = os.open(os.path.join(APP, name), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return None
    with os.fdopen(fd, "rb") as f:
        st = os.fstat(f.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_BYTES:
            return None
        return f.read()


def text(line: bytes) -> str:
    return line.decode("utf-8", "surrogateescape")


def find(lines: list[bytes], key: str) -> list[bytes]:
    """Every line that is the entry `  key: ...` (two spaces, key, colon)."""
    prefix = f"  {key}:".encode()
    return [ln for ln in lines if ln.startswith(prefix)]


def project(line: bytes, wanted: set[int]) -> list[tuple[int, int]]:
    """(offset, code point) of each wanted character, by decoded offset."""
    return [(i, ord(c)) for i, c in enumerate(text(line)) if ord(c) in wanted]


def same_projection(gold: list[bytes], got: list[bytes], keys: list[str], proj) -> bool:
    for key in keys:
        g, s = find(gold, key), find(got, key)
        if len(g) != 1 or len(s) != 1 or proj(g[0]) != proj(s[0]):
            return False
    return True


def expected_ops(gold_ts: list[bytes]) -> set[tuple]:
    """The only non-equal opcodes a correct edit of strings.ts produces, in golden indexes."""
    v = gold_ts.index(OLD_VERSION.encode())
    a = next(i for i, ln in enumerate(gold_ts) if ln.startswith(f"  {ANCHOR_KEY}:".encode()))
    return {
        ("replace", v, v + 1, (OLD_VERSION.encode(),), (NEW_VERSION.encode(),)),
        ("insert", a + 1, a + 1, (), (ENTRY.encode(),)),
    }


def only_allowed_changes(gold: list[bytes], got: list[bytes], allowed: set[tuple]) -> bool:
    sm = difflib.SequenceMatcher(None, gold, got, autojunk=False)
    return all(
        (tag, i1, i2, tuple(gold[i1:i2]), tuple(got[j1:j2])) in allowed
        for tag, i1, i2, j1, j2 in sm.get_opcodes()
        if tag != "equal"
    )


def valid_utf8(data: bytes) -> bool:
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def grade(app: dict[str, bytes | None], gold: dict[str, bytes]) -> dict[str, bool]:
    report = dict.fromkeys(CHECKS, False)
    if any(app[n] is None for n in FILES):
        return report
    ts, csv, readme = app[TS], app[CSV], app[README]
    g_ts, g_csv = gold[TS].split(b"\n"), gold[CSV].split(b"\n")
    s_ts, s_csv = ts.split(b"\n"), csv.split(b"\n")

    report["version_bumped"] = s_ts.count(NEW_VERSION.encode()) == 1 and (
        s_ts.count(OLD_VERSION.encode()) == 0
    )
    anchor = [i for i, ln in enumerate(s_ts) if ln.startswith(f"  {ANCHOR_KEY}:".encode())]
    report["entry_inserted"] = (
        s_ts.count(ENTRY.encode()) == 1
        and len(anchor) == 1
        and s_ts[anchor[0] + 1 : anchor[0] + 2] == [ENTRY.encode()]
    )
    records = [ln.removesuffix(b"\r") for ln in s_csv[:-1]]
    gold_records = [ln.removesuffix(b"\r") for ln in g_csv[:-1]]
    report["csv_row_appended"] = records == [*gold_records, ROW.encode()]

    row_line = ROW.encode() + b"\r"
    csv_allowed = {("insert", len(g_csv) - 1, len(g_csv) - 1, (), (row_line,))}
    report["untouched_lines_identical"] = only_allowed_changes(
        g_ts, s_ts, expected_ops(g_ts)
    ) and only_allowed_changes(g_csv, s_csv, csv_allowed)

    report["bidi_controls_preserved"] = same_projection(
        g_ts, s_ts, BIDI_KEYS, lambda ln: project(ln, BIDI)
    )
    report["zwj_zwnj_preserved"] = same_projection(g_ts, s_ts, ZW_KEYS, lambda ln: project(ln, ZW))
    whole = text
    report["mark_order_preserved"] = same_projection(g_ts, s_ts, MARK_KEYS, whole)
    report["nfd_line_preserved"] = same_projection(g_ts, s_ts, NFD_KEYS, whole)
    report["nfkc_char_kept"] = same_projection(
        g_ts, s_ts, KEPT_KEYS, lambda ln: [*project(ln, KEPT), text(ln)]
    )
    report["no_final_newline_added"] = not ts.endswith(b"\n") and ts.endswith(g_ts[-1])
    # CSV: every LF is part of a CRLF, nothing but CRLF ends a line, the file ends with one;
    # strings.ts keeps its LF-only endings
    report["crlf_preserved"] = (
        csv.endswith(b"\r\n")
        and csv.count(b"\n") == csv.count(b"\r") == csv.count(b"\r\n")
        and b"\r" not in ts
    )
    report["no_bom"] = not any(app[n].startswith(b"\xef\xbb\xbf") for n in FILES)
    report["valid_utf8"] = all(valid_utf8(app[n]) for n in FILES)
    report["readme_unchanged"] = readme == gold[README]
    return report


def main() -> None:
    reachable = unlocked_path(HERE)
    if reachable is not None:
        print(f"refusing to grade: grader files readable by others: {reachable}", file=sys.stderr)
        sys.exit(2)
    sweep()
    app = {name: read_app(name) for name in FILES}  # one snapshot; later writes do not count
    sweep()
    gold = {}
    for name in FILES:
        with open(os.path.join(GOLDEN, name), "rb") as f:
            gold[name] = f.read()
    report = grade(app, gold)
    unreadable = [n for n in FILES if app[n] is None]
    reason = f"unreadable app file: {', '.join(unreadable)}" if unreadable else None
    log_checks(report, DETAIL, reason)
    print(json.dumps(report, indent=1))
    sys.exit(0 if all(report.values()) else 1)


main()
