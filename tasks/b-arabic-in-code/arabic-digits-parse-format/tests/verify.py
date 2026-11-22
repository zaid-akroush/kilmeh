"""Track B parent grader for arabic-digits-parse-format. Never imports anything from the app.

Draws every input at random for each run (see make_case), runs tests/worker.py (as uid 65534 in
a new session when this process is root) to get the agent's raw outputs, compares them with
values computed here, then kills the worker's process group and, when root, every process left
under uid 65534. Prints one boolean per check as JSON and exits 0 only if all pass. Run with
`python3 -I -S` (see test.sh).

Why a forged worker output cannot pass: the agent's module runs inside the worker and can write
anything to the worker's result channel. But the templates below are fixed and public, while
the digits in them are redrawn here for each run (SystemRandom) and sent on stdin, and the
expected values are computed here from the drawn inputs. So the only output that passes is the
right answer for inputs the code never saw. Remaining limit: code in the worker could still
read the inputs from the worker's own memory.

Fails closed: before any agent code runs, the tests directory and everything in it must be
owned by the grading user (root in the container) with no group or other access, or verify
exits 2 with the reason on stderr. The worker therefore cannot read this file, so its source
is passed with `-c`.

The hidden inputs are a strict superset of the six examples in fixture/test_numerals.py.
Source is ASCII only: non-ASCII characters are written as escapes.
"""

import json
import os
import random
import re
import signal
import subprocess
import sys
import tempfile
import unicodedata
from decimal import ROUND_HALF_EVEN, Decimal, localcontext

APP = os.environ.get("KILMEH_APP", "/app")
HERE = os.path.dirname(os.path.abspath(__file__))
WORKER = os.path.join(HERE, "worker.py")
WORKER_TIMEOUT = 60
MAX_OUTPUT = 4_000_000
NOBODY = 65534
RNG = random.SystemRandom()
ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin"}

ARAB = "".join(map(chr, range(0x0660, 0x066A)))
EXT = "".join(map(chr, range(0x06F0, 0x06FA)))
SYSTEMS = {"latn": None, "arab": ARAB, "arabext": EXT}


def east(text: str, digits: str, decimal: str = "\u066b") -> str:
    """Write a Western template in Eastern digits: "," -> U+066C, "." -> `decimal`."""
    return text.translate(str.maketrans("0123456789,.", digits + "\u066c" + decimal))


def in_system(text: str, system: str) -> str:
    return text if system == "latn" else east(text, SYSTEMS[system])


# Templates: (call, kind). The expected value of each drawn call is computed by `expect`; the
# second value in value(...) and the Western text in the format lists document the template.
def value(text, _documented=None):
    return ("parse", text), "value"


def reject(text):
    return ("parse", text), "reject"


# Plain integers (no separators). Only these cases carry surrounding spaces.
PLAIN = [
    ("0", "0"),
    ("7", "7"),
    ("42", "42"),
    ("007", "7"),
    ("1234567", "1234567"),
    ("  12 ", "12"),
    (" -15", "-15"),
    ("-8   ", "-8"),
    ("1234567890123456789012345", "1234567890123456789012345"),
]

PARSE_DECIMAL_SEP = [
    value("3.14", "3.14"),
    value("-0.5", "-0.5"),
    value("10.250", "10.25"),
    value("0.001", "0.001"),
    value(east("3.14", ARAB), "3.14"),
    value(east("3.14", ARAB, "."), "3.14"),
    value(east("-0.5", ARAB), "-0.5"),
    value(east("10.250", ARAB, "."), "10.25"),
    value(east("3.14", EXT), "3.14"),
    value(east("3.14", EXT, "."), "3.14"),
    value(east("10.250", EXT), "10.25"),
]

# Eastern decimals here use U+066B only. Five or more grouping separators appear only here.
PARSE_GROUPING = [
    value("1,234", "1234"),
    value("-1,000", "-1000"),
    value("1,234.5", "1234.5"),
    value("12,345,678.9", "12345678.9"),
    value("1,234,567,890,123,456,789", "1234567890123456789"),
    value("-999,999,999,999,999,999.25", "-999999999999999999.25"),
    value(east("1,234", ARAB), "1234"),
    value(east("12,345,678.9", ARAB), "12345678.9"),
    value(east("1,234,567,890,123,456,789", ARAB), "1234567890123456789"),
    value(east("12,345", EXT), "12345"),
    value(east("1,234.5", EXT), "1234.5"),
    value(east("-1,234,567,890,123,456,789.5", EXT), "-1234567890123456789.5"),
]

REJECTS_MIXED = [
    reject("1\u0662\u0663"),  # Western 1, Arabic-Indic 2 3 (visible example)
    reject("1\u0662"),
    reject("\u0661\u06f2"),  # Arabic-Indic then Extended
    reject("\u06f12"),
    reject("1,\u0662\u0663\u0664"),
    reject("\u0661\u066c234"),
    reject("1\u066c234"),  # Western digits, Arabic thousands separator
    reject("3\u066b14"),  # Western digits, Arabic decimal separator
    reject("\u0661,\u0662\u0663\u0664"),  # Arabic-Indic digits, Western comma
    reject("\u0661\u0662\u0663.4"),
    reject("-\u06612"),
    reject("\u06f1\u066c\u0662\u0663\u0664"),
]

REJECTS_OTHER_DIGITS = [
    reject("\u0967\u0968\u0969"),  # Devanagari
    reject("-\u0967"),
    reject("\uff11\uff12\uff13"),  # fullwidth
    reject("\u00b2"),  # superscript two
    reject("\u00b9\u00b2"),
    reject("\u09e7\u09e8"),  # Bengali
    reject("\u07c1\u07c2"),  # NKo
    reject("\U0001d7cf\U0001d7d0"),  # mathematical bold
    reject("\u0e51\u0e52"),  # Thai
    reject("\u2460"),  # circled one
]

REJECTS_EXTRAS = [
    reject(""),
    reject("   "),
    reject("-"),
    reject("1_000"),
    reject("\u0661_\u0660\u0660\u0660"),
    reject("1 000"),
    reject("12 3"),
    reject("- 5"),
    reject("+5"),
    reject("1e3"),
    reject("1E3"),
    reject("NaN"),
    reject("nan"),
    reject("Infinity"),
    reject("inf"),
    reject("-inf"),
    reject(".5"),
    reject("5."),
    reject("\u066b\u0665"),
    reject("--5"),
    reject("5-"),
    reject("\t5"),
    reject("5\n"),
    reject("\u00a05"),  # no-break space
    reject("\u22125"),  # minus sign
    reject("0x10"),
]

REJECTS_BAD_GROUPING = [
    reject("1,23"),
    reject("12,34,567"),
    reject("1,2345"),
    reject(",123"),
    reject("123,"),
    reject("1,,234"),
    reject("1234,567"),
    reject("1,234,56"),
    reject("1.234,5"),
    reject("1,234.567,8"),
    reject("1,234."),
    reject("-,123"),
    reject(east("1,23", ARAB)),
    reject(east("1234,567", EXT)),
]

# (value, places or None for the default, Western expected). Positive places=3 only here.
FORMAT_BASIC = [
    (0, 0, "0"),
    (7, 0, "7"),
    (999, 0, "999"),
    (1000, 0, "1,000"),
    (1000000, 0, "1,000,000"),
    ("1234567.891", 2, "1,234,567.89"),
    ("12.5", 3, "12.500"),
    ("1234567.5", 3, "1,234,567.500"),
    ("0.07", 2, "0.07"),
    (123456789, 2, "123,456,789.00"),
    ("42.9", None, "43"),
]


def format_cases(system):
    cases = []
    for v, places, expected in FORMAT_BASIC:
        call = ("format", v, system) if places is None else ("format", v, system, places)
        cases.append((call, "text"))
    return cases


def fmt(v, system, places, _documented):
    return ("format", v, system, places), "text"


FORMAT_NEGATIVE_AND_ROUNDING = [
    fmt("-1234.5", "latn", 0, "-1,234"),
    fmt("2.5", "latn", 0, "2"),
    fmt("3.5", "latn", 0, "4"),
    fmt("-0.5", "latn", 0, "0"),
    fmt("-0.004", "latn", 2, "0.00"),
    fmt("-0.0", "latn", 1, "0.0"),
    fmt("1.005", "latn", 2, "1.00"),
    fmt("-999.995", "latn", 2, "-1,000.00"),
    fmt(-7, "latn", 0, "-7"),
    fmt("-12345.675", "arab", 2, "-" + east("12,345.68", ARAB)),
    fmt("0.125", "arabext", 2, east("0.12", EXT)),
    fmt(-1000000, "arabext", 0, "-" + east("1,000,000", EXT)),
]


def roundtrip_cases():
    """300 random values x 3 systems: parse(format(x, system, places)) must equal x."""
    rng = RNG
    cases = []
    for _ in range(300):
        digits = rng.randint(1, 15)
        integer = rng.randrange(10 ** (digits - 1) if digits > 1 else 0, 10**digits)
        places = rng.choice((0, 2, 6))
        fraction = rng.randrange(10**places) if places else 0
        sign = "-" if (integer or fraction) and rng.random() < 0.5 else ""
        text = sign + str(integer) + (f".{fraction:0{places}d}" if places else "")
        v = int(text) if places == 0 else text
        for system in SYSTEMS:
            cases.append((("roundtrip", v, system, places), "value"))
    return cases


def total(amounts, system, _documented):
    return ("total", amounts, system), "text"


CALLER = [
    total(["1,200.50", east("300.25", ARAB), east("499.25", EXT)], "arab", east("2,000.00", ARAB)),
    total(["-50.00", "20"], "latn", "-30.00"),
    total([east("1,234,567.89", EXT), "0.11"], "arabext", east("1,234,568.00", EXT)),
    total(["999.99", east("0.01", ARAB)], "latn", "1,000.00"),
    total([], "latn", "0.00"),
]

# Fixed templates per check; make_case redraws their digits for each run.
TEMPLATES = {
    "parse_latn": [value(t, e) for t, e in PLAIN],
    "parse_arab": [value(east(t, ARAB), e) for t, e in PLAIN],
    "parse_arabext": [value(east(t, EXT), e) for t, e in PLAIN],
    "parse_decimal_sep": PARSE_DECIMAL_SEP,
    "parse_grouping": PARSE_GROUPING,
    "rejects_mixed_scripts": REJECTS_MIXED,
    "rejects_other_unicode_digits": REJECTS_OTHER_DIGITS,
    "rejects_python_int_extras": REJECTS_EXTRAS,
    "rejects_bad_grouping": REJECTS_BAD_GROUPING,
    "format_latn": format_cases("latn"),
    "format_arab": format_cases("arab"),
    "format_arabext": format_cases("arabext"),
    "format_negative_and_rounding": FORMAT_NEGATIVE_AND_ROUNDING,
    "roundtrip_seeded": [],  # drawn whole in make_case
    "caller_works": CALLER,
}

CHECKS = list(TEMPLATES)
DETAIL = {
    "parse_latn": "parse Western-digit integers",
    "parse_arab": "parse Arabic-Indic integers",
    "parse_arabext": "parse Extended Arabic-Indic integers",
    "parse_decimal_sep": "parse decimals with '.' or U+066B",
    "parse_grouping": "parse grouped numbers (',' or U+066C)",
    "rejects_mixed_scripts": "reject mixed digit scripts and separators",
    "rejects_other_unicode_digits": "reject non-Arabic Unicode digits",
    "rejects_python_int_extras": "reject what int()/Decimal() accept but the spec does not",
    "rejects_bad_grouping": "reject malformed grouping",
    "format_latn": "format in Western digits",
    "format_arab": "format in Arabic-Indic digits",
    "format_arabext": "format in Extended Arabic-Indic digits",
    "format_negative_and_rounding": "format negatives with half-even rounding",
    "roundtrip_seeded": "parse(format(x)) == x for random values",
    "caller_works": "invoice total_text sums mixed-script amounts",
}
SWAP = "1234678"  # 0, 5 and 9 stay put: they carry the zero, tie and carry edge cases


def redraw(text: str) -> str:
    """Replace each decimal digit (any script) in SWAP by a random SWAP digit of the same
    script, so length, script, separators, zeros, ties and carries keep their places."""
    out = []
    for ch in text:
        d = unicodedata.decimal(ch, None)
        if d is not None and str(d) in SWAP:
            ch = chr(ord(ch) - d + int(RNG.choice(SWAP)))
        out.append(ch)
    return "".join(out)


def redraw_arg(arg):
    if isinstance(arg, list):
        return [redraw(a) for a in arg]
    if isinstance(arg, int):
        return int(redraw(str(arg)))
    return redraw(arg)


def parsed(text: str) -> Decimal:
    """Value of a well-formed number (only called on templates that are valid by design)."""
    s = text.strip(" ").replace(",", "").replace("\u066c", "").replace("\u066b", ".")
    return Decimal("".join(str(unicodedata.decimal(c)) if c.isdigit() else c for c in s))


def formatted(v, system: str, places: int) -> str:
    with localcontext() as ctx:
        ctx.prec = 100
        q = Decimal(v).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    return in_system(format(abs(q) if q == 0 else q, ",f"), system)


def expect(call: list, kind: str) -> tuple:
    if kind == "reject":
        return ("reject",)
    if call[0] == "parse":
        return ("value", str(parsed(call[1])))
    if call[0] == "roundtrip":
        return ("value", str(call[1]))
    if call[0] == "format":
        return ("text", formatted(call[1], call[2], call[3] if len(call) > 3 else 0))
    amounts = sum((parsed(a) for a in call[1]), Decimal(0))
    return ("text", formatted(amounts, call[2], 2))


def make_case() -> dict:
    """check -> [(call, expected)], every digit drawn for this run."""
    case = {}
    for key, cases in TEMPLATES.items():
        drawn = [([c[0], redraw_arg(c[1]), *c[2:]], kind) for c, kind in cases]  # not places
        if key == "roundtrip_seeded":
            drawn = [(list(c), kind) for c, kind in roundtrip_cases()]
        case[key] = [(call, expect(call, kind)) for call, kind in drawn]
    return case


_DECIMAL_STR = re.compile(r"-?\d+(?:\.\d+)?(?:E[+-]\d+)?", re.ASCII)


def matches(result, expect) -> bool:
    if not (isinstance(result, list) and all(isinstance(x, str) for x in result)):
        return False
    if expect[0] == "reject":
        return result == ["err", "ValueError"]
    if expect[0] == "text":
        return result == ["ok", "str", expect[1]]
    if len(result) != 3 or result[:2] != ["ok", "Decimal"]:
        return False
    if not _DECIMAL_STR.fullmatch(result[2]):
        return False
    return Decimal(result[2]) == Decimal(expect[1])


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


def main() -> None:
    reachable = unlocked_path(HERE)
    if reachable is not None:
        print(f"refusing to grade: grader files readable by others: {reachable}", file=sys.stderr)
        sys.exit(2)
    calls, owners = [], []
    for key, cases in make_case().items():
        for call, expected in cases:
            calls.append(call)
            owners.append((key, expected))
    results = run_worker(APP, calls)
    # The verifier log keeps the raw exchange (tests compare runs; the grade never reads it).
    print("worker calls:", json.dumps(calls), file=sys.stderr)
    print("worker results:", json.dumps(results), file=sys.stderr)
    report = dict.fromkeys(CHECKS, True)
    for i, (key, expected) in enumerate(owners):
        if results is None or not matches(results[i], expected):
            report[key] = False
    log_checks(report, DETAIL, "no well-formed worker output" if results is None else None)
    print(json.dumps(report, indent=1))
    sys.exit(0 if all(report.values()) else 1)


main()
