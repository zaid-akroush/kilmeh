"""Known-bad numerals.py (solve.sh copies this file over /app/numerals.py).

Plausible mistake: parsing leans on Decimal(), which already accepts any Unicode decimal digit
(mixed systems, Devanagari, fullwidth), underscores, "+", exponents, NaN, "5." and surrounding
whitespace of any kind. The grouping regex uses \\d, which matches every Unicode digit too.
Formatting is correct. Must FAIL the rejection checks.
"""

import re
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation, localcontext

_GROUPED = re.compile(r"-?\d{1,3}(?:[,\u066c]\d{3})+(?:[.\u066b]\d+)?")
DIGITS = {
    "latn": "0123456789",
    "arab": "".join(map(chr, range(0x0660, 0x066A))),
    "arabext": "".join(map(chr, range(0x06F0, 0x06FA))),
}


def parse_number(text: str) -> Decimal:
    s = text.strip(" ")
    if ("," in s or "\u066c" in s) and not _GROUPED.fullmatch(s):
        raise ValueError(f"bad grouping: {text!r}")
    s = s.replace(",", "").replace("\u066c", "").replace("\u066b", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        raise ValueError(f"not a number: {text!r}") from None


def format_number(value, system: str, places: int = 0) -> str:
    digits = DIGITS[system]
    group, decimal_sep = ("," , ".") if system == "latn" else ("\u066c", "\u066b")
    value = Decimal(value)
    with localcontext() as ctx:
        ctx.prec = max(28, value.adjusted() + places + 2)
        rounded = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    sign = "-" if rounded < 0 else ""
    integer, _, fraction = f"{abs(rounded):f}".partition(".")
    grouped = f"{int(integer):,}".replace(",", group)
    text = grouped + (decimal_sep + fraction if places else "")
    return sign + text.translate(str.maketrans("0123456789", digits))
