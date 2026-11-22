"""Track B parent grader for arabic-search-normalize. Never imports anything from the app.

Draws every input at random for each run (see below), runs tests/worker.py (as uid 65534 in a
new session when this process is root) to get the agent's raw outputs, compares them with
values computed here, then kills the worker's process group and, when root, every process left
under uid 65534. Prints one boolean per check as JSON and exits 0 only if all pass. Run with
`python3 -I -S` (see test.sh).

Why a forged worker output cannot pass: the agent's module runs inside the worker process and
can write anything to the worker's result channel. But the records, queries, normalize inputs
and sort sets are generated here, at random, for each run and sent on stdin, and the expected
results are computed here with `norm` (an independent copy of the specified rules: Mn ranges
of U+0600-U+06FF, Unicode 15.0). So the only output that passes is the right answer for inputs
the code never saw, i.e. the behaviour. Remaining limit: code in the worker process could
still read the inputs from the worker's own memory and compute answers from them.

Fails closed: before any agent code runs, the tests directory and everything in it must be
owned by the grading user (root in the container) with no group or other access, or verify
exits 2 with the reason on stderr.

Invisible and combining characters are written with chr(); the source stays escape-clean.
"""

import hashlib
import json
import os
import random
import signal
import string
import subprocess
import sys
import tempfile

APP = os.environ.get("KILMEH_APP", "/app")
HERE = os.path.dirname(os.path.abspath(__file__))
WORKER = os.path.join(HERE, "worker.py")
WORKER_TIMEOUT = 60
MAX_OUTPUT = 4_000_000
NOBODY = 65534
ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin"}

_MN = [
    r
    for lo, hi in [
        (0x610, 0x61A),
        (0x64B, 0x65F),
        (0x670, 0x670),
        (0x6D6, 0x6DC),
        (0x6DF, 0x6E4),
        (0x6E7, 0x6E8),
        (0x6EA, 0x6ED),
    ]
    for r in range(lo, hi + 1)
]
_TABLE = {c: None for c in _MN}
_TABLE[0x640] = None
_TABLE.update(str.maketrans("أإآٱةى", "ااااهي"))


def norm(s: str) -> str:
    return s.translate(_TABLE).casefold()


# Every input is drawn at random for each run (secrets-grade), so a forged worker output cannot
# be precomputed: the expected values below are computed here, with `norm`, from inputs the
# agent's code never saw. The structure is fixed (each check always gets its own feature, every
# range endpoint, negatives, NFD, the over-normalization traps) and the letters are random.
RNG = random.SystemRandom()
# Letters that no rule touches (no alef forms, haa, yaa, taa marbuta, maqsura, hamza letters).
POOL = "بتثجحخدذرزسشصضطظعغفقكلمنو"
TATWEEL = chr(0x640)
LIGATURE = chr(0xFDF2)
WASLA = chr(0x671)
HAMZA_ALEFS = "أإآ" + WASLA
MN_ENDPOINTS = [0x610, 0x61A, 0x64B, 0x65F, 0x670, 0x6D6, 0x6DC, 0x6DF, 0x6E4, 0x6E7, 0x6E8]
MN_ENDPOINTS += [0x6EA, 0x6ED]  # first and last code point of each of the 7 Mn ranges
TASHKEEL = list(range(0x64B, 0x653))  # not U+0653 to U+0655: only nfd_input uses those
NOT_MN_NEXT_TO_RANGES = [0x61B, 0x64A, 0x660, 0x6D5, 0x6DD, 0x6DE, 0x6E6, 0x6E9, 0x6EE]
PERSIAN = [chr(c) for c in (0x67E, 0x686, 0x698, 0x6AF, 0x6A9, 0x6CC)]
ALLAH = "الله"
LATIN = string.ascii_letters


def word(lo: int = 2, hi: int = 5) -> str:
    return "".join(RNG.choice(POOL) for _ in range(RNG.randint(lo, hi)))


def latin(lo: int = 3, hi: int = 7) -> str:
    return "".join(RNG.choice(LATIN) for _ in range(RNG.randint(lo, hi)))


def put(w: str, piece: str) -> str:
    """Insert `piece` after a random letter of `w` (never first, so a mark has a base)."""
    i = RNG.randint(1, len(w))
    return w[:i] + piece + w[i:]


def sandwich(piece: str) -> str:
    return word(1, 3) + piece + word(1, 3)


def norm_inputs() -> dict[str, list[str]]:
    """Inputs per normalize check; the expected output of each is norm(input)."""
    tashkeel_all = "".join(RNG.choice(POOL) + chr(c) for c in TASHKEEL)
    others = [0x670, 0x6D6, 0x6DC, 0x6E1, 0x6E2, 0x610, 0x61A]
    return {
        "strips_tashkeel": [
            *[sandwich(chr(c)) for c in MN_ENDPOINTS],
            tashkeel_all,
            *[
                put(word(3, 5), "".join(chr(RNG.choice(TASHKEEL + others)) for _ in range(3)))
                for _ in range(3)
            ],
            "".join(chr(c) for c in RNG.sample(MN_ENDPOINTS, 4)),
        ],
        "strips_tatweel": [
            *[put(word(3, 5), TATWEEL * RNG.randint(1, 4)) for _ in range(4)],
            TATWEEL * RNG.randint(1, 5),
            latin(1, 2).lower() + TATWEEL + latin(1, 2).lower(),
        ],
        "alef_variants": [
            *[ch + word() for ch in HAMZA_ALEFS],
            *[sandwich(ch) for ch in HAMZA_ALEFS],
            "".join(RNG.sample(HAMZA_ALEFS, 4)),
        ],
        "taa_marbuta": [
            word() + "ة",
            "ة" + word(),
            sandwich("ة"),
            "ة" * RNG.randint(1, 3),
        ],
        "alef_maqsura": [
            word() + "ى",
            "ى" + word(),
            sandwich("ى"),
            "ى" * RNG.randint(1, 3),
        ],
        "nfd_input": [
            *[word() + "ا" + chr(m) + word() for m in (0x653, 0x654, 0x655)],
            *["ا" + chr(m) + word() for m in (0x653, 0x654, 0x655)],
            word() + "و" + chr(0x654),
            sandwich("ي" + chr(0x654)),
        ],
        "no_over_normalization": [
            *[sandwich(ch) for ch in "ؤئء"],
            sandwich(LIGATURE),
            word() + " " + LIGATURE,
            *[sandwich(RNG.choice(PERSIAN)) for _ in range(3)],
            word() + "ك" + chr(0x6E5),
            *[sandwich(chr(c)) for c in NOT_MN_NEXT_TO_RANGES],
        ],
        "latin_casefold": [
            latin(),
            latin() + " " + latin(),
            "Stra" + "ß" + "e",
            latin(1, 3) + "ß" + latin(1, 3),
            latin(1, 3) + "e" + chr(0x301),  # NFKC would compose this
            latin() + " " + word(),
        ],
    }


def decorate(text: str) -> str:
    """Respell `text` with variants that must all normalize alike (hamza forms of alef, taa
    marbuta for haa, maqsura for yaa, random tashkeel and tatweel)."""
    out = []
    for ch in text:
        if ch == "ا":
            ch = RNG.choice("اأإآ" + WASLA)
        elif ch == "ه":
            ch = RNG.choice("هة")
        elif ch == "ي":
            ch = RNG.choice("يى")
        out.append(ch)
        if ch not in " " and RNG.random() < 0.25:
            out.append(chr(RNG.choice(TASHKEEL)) if RNG.random() < 0.6 else TATWEEL)
    return "".join(out)


def make_rows() -> list[dict]:
    """About 30 records: fixed kinds of trap, random words."""
    b1, b2, b3, b4, b5 = word(2, 3), word(2, 3), word(2, 3), word(2, 3), word(2, 3)
    names = [
        f"{word()} {ALLAH} {word()}",
        f"{word()} {LIGATURE} {word()}",
        b1 + "ؤ" + b2,
        b1 + "و" + b2,
        b3 + "ئ" + b4,
        b3 + "ي" + b4,
        b5 + "ء",
        b5 + "و",
        b1 + "ک" + b2,
        b1 + "ك" + b2,
        word() + "ا" + chr(0x654) + word(),
        f"{latin()} {latin()}",
        f"{latin().upper()} {latin().lower()}",
        decorate(word(3, 5) + "ه " + word(3, 5)),
        word(3, 5) + "ة " + word(3, 5),
        word(3, 5) + "ى " + word(3, 5),
        word(3, 5) + "ي " + word(3, 5),
        "أ" + word() + " " + word(),
        "ا" + word() + " " + word(),
        "إ" + word() + " " + word(),
    ]
    names += [f"{word()} {word()}" for _ in range(10)]
    RNG.shuffle(names)
    cities = [word(3, 5) for _ in names]
    cities[RNG.randrange(len(names))] = latin(4, 6)
    cities[RNG.randrange(len(names))] = decorate("ا" + word(2, 4) + "ه")
    ids = RNG.sample(range(1000, 100000), len(names))  # random, so forged hits cannot agree
    return [{"id": i, "name": n, "city": c} for i, n, c in zip(ids, names, cities, strict=True)]


def make_queries(rows: list[dict]) -> list[str]:
    queries = []
    for _ in range(26):  # substrings of real fields, respelled
        field = RNG.choice(rows)[RNG.choice(("name", "city"))]
        w = RNG.choice(field.split())
        i = RNG.randrange(len(w))
        queries.append(decorate(w[i : i + RNG.randint(2, 5)]))
    for _ in range(4):  # across a space
        name = RNG.choice(rows)["name"].split()
        queries.append(decorate(" ".join(name[:2])))
    queries += [ALLAH, LIGATURE, decorate(ALLAH)]
    sample = RNG.sample(rows, 6)
    queries += [r["name"] for r in sample[:3]] + [r["city"] for r in sample[3:]]
    queries += [r["name"].split()[0].swapcase() for r in rows if r["name"].isascii()]
    for row in rows:  # one lookalike pair from the traps: hits one record, not the other
        for trap in "ؤئءک":  # not in POOL, so exactly four rows
            if trap in row["name"]:
                queries.append(row["name"])
                break
    queries += [
        latin(4, 8),  # negatives from here on
        latin(3, 5).lower(),
        word(5, 7),
        word(5, 7),
        "",
        chr(0x64B) + TATWEEL,
        TATWEEL * 2,
        decorate(ALLAH).replace("ا", "", 1),  # near miss
        RNG.choice(PERSIAN) + word(2, 3),
    ]
    return queries


def make_sort_sets() -> list[list[str]]:
    w1, w2, w3 = word(2, 4), word(2, 4), word(2, 4)
    ties = [p + w1 for p in ("ا", "أ", "إ", "آ", WASLA)] + [decorate("ا" + w1), "ا" + w1]
    sets = [
        # alef wasla before ba, and taa marbuta after taa, only in normalized order
        ties + [WASLA + w2, "ب" + w2, "ة" + w3, "ت" + w3, word(), word()],
        [*RNG.sample("بتثجحخدذرزس", 5), "ٱ", "ء", "ي", "ى", "ئ", "ة", "ه", "آ", "أ", "ا"],
        [latin(), latin().upper(), latin().lower(), latin(), word(), "أ" + word()],
        [decorate(w3), w3, w3, decorate(w3), decorate(w3)],
        [word(2, 5) for _ in range(12)],
        [],
        [word()],
    ]
    for s in sets:
        RNG.shuffle(s)
    return sets


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


def _as_nobody() -> dict:
    """Drop to uid 65534 when root. Not root: no drop, process-group kill only."""
    if os.geteuid() != 0:
        return {}
    return {"user": NOBODY, "group": NOBODY, "extra_groups": []}


def _kill_nobody() -> None:
    """kill(-1) run as uid 65534 signals every process of that uid, including daemons that
    left the worker's session. Only used when root."""
    for _ in range(3):
        subprocess.run(
            [sys.executable, "-I", "-S", "-c", "import os, signal; os.kill(-1, signal.SIGKILL)"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd="/",
            env=ENV,
            timeout=30,
            **_as_nobody(),
        )


def run_worker(app: str, calls: list) -> list | None:
    """Raw results, one per call, or None if the worker gave no well-formed answer."""
    with tempfile.TemporaryFile() as fin, tempfile.TemporaryFile() as fout:
        fin.write(json.dumps(calls).encode("ascii"))
        fin.seek(0)
        with open(WORKER, encoding="ascii") as f:
            worker_source = f.read()
        proc = subprocess.Popen(
            [sys.executable, "-I", "-S", "-c", worker_source, app],
            stdin=fin,
            stdout=fout,
            stderr=subprocess.DEVNULL,
            cwd=app,
            env=ENV,
            start_new_session=True,
            **_as_nobody(),
        )
        try:
            proc.wait(timeout=WORKER_TIMEOUT)
        except subprocess.TimeoutExpired:
            pass
        finally:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except OSError:
                pass
            if os.geteuid() == 0:
                _kill_nobody()
            proc.wait()
        fout.seek(0)
        data = fout.read(MAX_OUTPUT + 1)
    if len(data) > MAX_OUTPUT:
        return None
    try:
        results = json.loads(data)
    except ValueError:
        return None
    if not isinstance(results, list) or len(results) != len(calls):
        return None
    return results


NORM_KEYS = [
    "strips_tashkeel",
    "strips_tatweel",
    "alef_variants",
    "taa_marbuta",
    "alef_maqsura",
    "nfd_input",
    "no_over_normalization",
    "latin_casefold",
]
SEARCH_KEYS = [
    "search_recall_hidden",
    "search_precision_hidden",
    "search_returns_originals",
    "records_not_mutated",
]
SORT_KEYS = ["sort_order_hidden", "sort_returns_originals"]
CHECKS = [*NORM_KEYS, *SEARCH_KEYS, *SORT_KEYS]
DETAIL = {
    "strips_tashkeel": "normalize strips the specified Mn marks",
    "strips_tatweel": "normalize strips tatweel",
    "alef_variants": "normalize folds hamza alef forms to bare alef",
    "taa_marbuta": "normalize folds taa marbuta to haa",
    "alef_maqsura": "normalize folds alef maqsura to yaa",
    "nfd_input": "normalize handles decomposed (NFD) input",
    "no_over_normalization": "normalize leaves other letters and marks alone",
    "latin_casefold": "normalize casefolds Latin without NFKC",
    "search_recall_hidden": "search finds every matching record",
    "search_precision_hidden": "search returns no extra or duplicate records",
    "search_returns_originals": "search returns the input records, in input order",
    "records_not_mutated": "search leaves the records unchanged",
    "sort_order_hidden": "sort orders by normalized form",
    "sort_returns_originals": "sort returns the original strings",
}


def log_checks(report: dict[str, bool], detail: dict[str, str], reason: str | None) -> None:
    """One `PASS key: detail` / `FAIL key: detail` line per check on stderr, in report order
    (the RTL graders' format). Details are fixed text: no input or expected value is printed."""
    for key, ok in report.items():
        why = detail[key] if ok else reason or f"expected {detail[key]}"
        print(f"{'PASS' if ok else 'FAIL'} {key}: {why}", file=sys.stderr)


def expected_ids(rows: list[dict], query: str) -> list[int]:
    q = norm(query)
    if not q:
        return []
    return [r["id"] for r in rows if q in norm(r["name"]) or q in norm(r["city"])]


def make_case() -> dict:
    inputs = norm_inputs()
    rows = make_rows()
    return {
        "norm": inputs,
        "rows": rows,
        "queries": make_queries(rows),
        "sorts": make_sort_sets(),
    }


def build_calls(case: dict) -> list:
    calls = [["norm", s] for key in NORM_KEYS for s in case["norm"][key]]
    calls += [["search", case["rows"], q] for q in case["queries"]]
    calls += [["sort", names] for names in case["sorts"]]
    return calls


def grade(results: list | None, case: dict) -> dict[str, bool]:
    """Compare the worker's raw results with expectations computed here from `case`."""
    report = dict.fromkeys(CHECKS, False)
    if results is None:
        return report
    at = 0

    def take(n):
        nonlocal at
        chunk = results[at : at + n]
        at += n
        return chunk

    for key in NORM_KEYS:
        inputs = case["norm"][key]
        got = take(len(inputs))
        report[key] = all(r == ["ok", norm(s)] for r, s in zip(got, inputs, strict=True))
    rows, queries = case["rows"], case["queries"]
    found = take(len(queries))
    ok = all(r[0] == "ok" for r in found)
    wants = [expected_ids(rows, q) for q in queries]
    ids = [[h[0] for h in r[1]] if r[0] == "ok" else [] for r in found]
    pairs = list(zip(wants, ids, strict=True))
    report["search_recall_hidden"] = ok and all(set(w) <= set(g) for w, g in pairs)
    report["search_precision_hidden"] = ok and all(
        set(g) <= set(w) and len(g) == len(set(g)) for w, g in pairs
    )
    # each hit must be the input record at its reported index (the id has to agree with the
    # records sent now), unchanged, in input order
    report["search_returns_originals"] = ok and all(
        all(0 <= h[1] < len(rows) and rows[h[1]]["id"] == h[0] for h in r[1])
        and [h[1] for h in r[1]] == sorted({h[1] for h in r[1]})
        for r in found
    )
    sent = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    report["records_not_mutated"] = ok and all(r[2] == sent for r in found)
    sorted_ = take(len(case["sorts"]))
    ok = all(r[0] == "ok" for r in sorted_)
    order = returns = ok
    for r, names in zip(sorted_, case["sorts"], strict=True):
        if not ok:
            break
        want = sorted(names, key=lambda n: (norm(n), n))
        originals = sorted(r[1]) == sorted(names)
        returns = returns and originals
        # Strings returned in normalized form still get their order graded, by normalized form.
        got_norm = [norm(x) for x in r[1]]
        order = order and (r[1] == want if originals else got_norm == [norm(x) for x in want])
    report["sort_order_hidden"] = order
    report["sort_returns_originals"] = returns
    return report


def main() -> None:
    reachable = unlocked_path(HERE)
    if reachable is not None:
        print(f"refusing to grade: grader files readable by others: {reachable}", file=sys.stderr)
        sys.exit(2)
    case = make_case()
    calls = build_calls(case)
    results = run_worker(APP, calls)
    # The verifier log keeps the raw exchange (tests compare runs; the grade never reads it).
    print("worker calls:", json.dumps(calls), file=sys.stderr)
    print("worker results:", json.dumps(results), file=sys.stderr)
    report = grade(results, case)
    log_checks(report, DETAIL, "no well-formed worker output" if results is None else None)
    print(json.dumps(report, indent=1))
    sys.exit(0 if all(report.values()) else 1)


main()
