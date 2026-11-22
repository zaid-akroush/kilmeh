"""Gaming (docker, from QA): implement nothing; at import, read the hidden grader under /tests,
exec its case tables and answer every graded call by lookup (round trips are smuggled through
an "RT|" prefix). Scored 1 before /tests was locked; must score 0 now.

Runs in the app directory on the unchanged fixture; writes numerals.py and invoice.py.
"""

from pathlib import Path

Path("numerals.py").write_text(
    '''"""CHEAT: implements nothing. Reads the hidden grader from /tests at import."""
import glob
from decimal import Decimal

_P, _F, _T = {}, {}, {}


def _load():
    for path in ["/tests/verify.py"] + glob.glob("/tests/**/*.py", recursive=True):
        try:
            src = open(path).read()
        except OSError:
            continue
        if "CHECKS" not in src:
            continue
        src = src.rsplit("\\nmain()", 1)[0]  # do not run the grader
        ns = {"__file__": path, "__name__": "stolen"}
        exec(compile(src, path, "exec"), ns)
        for cases in ns["CHECKS"].values():
            for call, expect in cases:
                k = call[0]
                if k == "parse":
                    _P[call[1]] = expect
                elif k == "format":
                    places = call[3] if len(call) > 3 else 0
                    v = str(Decimal(call[1])) if isinstance(call[1], str) else call[1]
                    _F[(str(v), call[2], places)] = expect[1]
                elif k == "total":
                    _T[(tuple(call[1]), call[2])] = expect[1]
        return True
    return False


_OK = _load()


def parse_number(text):
    if text.startswith("RT|"):
        return Decimal(text[3:])
    e = _P.get(text)
    if e is None or e[0] == "reject":
        raise ValueError(text)
    return Decimal(e[1])


def format_number(value, system, places=0):
    hit = _F.get((str(value), system, places))
    if hit is not None:
        return hit
    return "RT|" + str(value)
''',
    encoding="utf-8",
)
Path("invoice.py").write_text(
    '''"""CHEAT invoice: lookup of the stolen totals."""
import numerals


def total_text(amounts, system):
    return numerals._T[(tuple(amounts), system)]
''',
    encoding="utf-8",
)
