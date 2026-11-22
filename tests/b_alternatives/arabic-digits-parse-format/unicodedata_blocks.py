"""Alternative (a): a hand-written scanner using unicodedata.digit plus a per-character block
check. No regex. Formatting builds the digits by hand from an integer of scaled units.

Runs in the app directory on the unchanged fixture; writes numerals.py.
"""

from pathlib import Path

Path("numerals.py").write_text(
    """
import unicodedata
from decimal import ROUND_HALF_EVEN, Decimal, localcontext

BASES = {"latn": 0x30, "arab": 0x0660, "arabext": 0x06F0}
GROUP = {"latn": ",", "arab": "\\u066c", "arabext": "\\u066c"}
DECIMALS = {"latn": (".",), "arab": ("\\u066b", "."), "arabext": ("\\u066b", ".")}
OUT_DECIMAL = {"latn": ".", "arab": "\\u066b", "arabext": "\\u066b"}


def _system_of(ch):
    for name, base in BASES.items():
        if base <= ord(ch) <= base + 9:
            return name
    return None


def parse_number(text):
    s = text.strip(" ")
    negative = s.startswith("-")
    if negative:
        s = s[1:]
    systems = {_system_of(c) for c in s if _system_of(c)}
    if len(systems) != 1:
        raise ValueError(text)
    (system,) = systems
    integer, fraction, seen_decimal = [], [], False
    for c in s:
        if _system_of(c) == system:
            (fraction if seen_decimal else integer).append(str(unicodedata.digit(c)))
        elif c in DECIMALS[system] and not seen_decimal:
            seen_decimal = True
        elif c == GROUP[system] and not seen_decimal:
            integer.append(",")
        else:
            raise ValueError(text)
    whole = "".join(integer)
    if not whole or whole[0] == "," or (seen_decimal and not fraction):
        raise ValueError(text)
    if "," in whole:
        parts = whole.split(",")
        if not 1 <= len(parts[0]) <= 3 or any(len(p) != 3 for p in parts[1:]):
            raise ValueError(text)
    number = ("-" if negative else "") + whole.replace(",", "")
    if fraction:
        number += "." + "".join(fraction)
    return Decimal(number)


def format_number(value, system, places=0):
    base = BASES[system]
    with localcontext() as ctx:
        ctx.prec = 200
        units = int((Decimal(value) * (Decimal(10) ** places)).to_integral_value(ROUND_HALF_EVEN))
    sign = "-" if units < 0 else ""
    digits = str(abs(units)).rjust(places + 1, "0")
    whole, fraction = digits[: len(digits) - places], digits[len(digits) - places :]
    chunks = []
    while whole:
        chunks.insert(0, whole[-3:])
        whole = whole[:-3]
    out = GROUP[system].join(chunks) + (OUT_DECIMAL[system] + fraction if places else "")
    return sign + "".join(chr(base + int(c)) if c.isdigit() else c for c in out)
""",
    encoding="utf-8",
)
