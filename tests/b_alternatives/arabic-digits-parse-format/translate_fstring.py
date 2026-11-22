"""Alternative (b): a per-system full-match regex, then str.translate to Western digits.
Formats with f"{x:,.{places}f}" and translates the result.

Runs in the app directory on the unchanged fixture; writes numerals.py.
"""

from pathlib import Path

Path("numerals.py").write_text(
    """
import re
from decimal import Decimal

AR = "".join(chr(0x0660 + i) for i in range(10))
EXT = "".join(chr(0x06F0 + i) for i in range(10))
PATTERNS = {
    "latn": re.compile(r"-?(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\\.[0-9]+)?"),
    "arab": re.compile(f"-?(?:[{AR}]{{1,3}}(?:\\u066c[{AR}]{{3}})+|[{AR}]+)(?:[.\\u066b][{AR}]+)?"),
    "arabext": re.compile(
        f"-?(?:[{EXT}]{{1,3}}(?:\\u066c[{EXT}]{{3}})+|[{EXT}]+)(?:[.\\u066b][{EXT}]+)?"
    ),
}
TO_WESTERN = str.maketrans(AR + EXT + "\\u066b", "0123456789" * 2 + ".", ",\\u066c")
FROM_WESTERN = {
    "latn": str.maketrans("", ""),
    "arab": str.maketrans("0123456789,.", AR + "\\u066c\\u066b"),
    "arabext": str.maketrans("0123456789,.", EXT + "\\u066c\\u066b"),
}


def parse_number(text):
    s = text.strip(" ")
    if any(p.fullmatch(s) for p in PATTERNS.values()):
        return Decimal(s.translate(TO_WESTERN))
    raise ValueError(text)


def format_number(value, system, places=0):
    out = f"{Decimal(value):,.{places}f}"
    if out.startswith("-") and not out.strip("-0.,"):
        out = out[1:]  # a rounded zero has no sign
    return out.translate(FROM_WESTERN[system])
""",
    encoding="utf-8",
)
