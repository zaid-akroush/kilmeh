"""Reference numerals.py (solve.sh copies this file over /app/numerals.py).

Explicit digit maps and one full-match regex per system; Decimal arithmetic only, no float.
"""

import re
from decimal import ROUND_HALF_EVEN, Decimal, localcontext

# name -> (ten digits, grouping separator, decimal separators accepted by parse, output decimal)
SYSTEMS = {
    "latn": ("0123456789", ",", (".",), "."),
    "arab": ("".join(map(chr, range(0x0660, 0x066A))), "\u066c", ("\u066b", "."), "\u066b"),
    "arabext": ("".join(map(chr, range(0x06F0, 0x06FA))), "\u066c", ("\u066b", "."), "\u066b"),
}


def _pattern(digits: str, group: str, decimals: tuple[str, ...]) -> re.Pattern[str]:
    d = "[" + re.escape(digits) + "]"
    g = re.escape(group)
    dec = "|".join(re.escape(s) for s in decimals)
    return re.compile(rf"(-?)({d}{{1,3}}(?:{g}{d}{{3}})+|{d}+)(?:(?:{dec})({d}+))?")


_PARSERS = [
    (_pattern(digits, group, decs), str.maketrans(digits, "0123456789"))
    for digits, group, decs, _ in SYSTEMS.values()
]


def parse_number(text: str) -> Decimal:
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    s = text.strip(" ")
    for pattern, to_ascii in _PARSERS:
        m = pattern.fullmatch(s)
        if m:
            sign, integer, fraction = m.groups()
            integer = re.sub(r"\D", "", integer.translate(to_ascii))
            number = sign + integer + ("." + fraction.translate(to_ascii) if fraction else "")
            return Decimal(number)
    raise ValueError(f"not a number in one digit system: {text!r}")


def format_number(value, system: str, places: int = 0) -> str:
    if system not in SYSTEMS:
        raise ValueError(f"unknown system: {system!r}")
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise TypeError("value must be an int or a Decimal")
    if isinstance(places, bool) or not isinstance(places, int) or places < 0:
        raise ValueError("places must be an int >= 0")
    digits, group, _, decimal_sep = SYSTEMS[system]
    value = Decimal(value)
    with localcontext() as ctx:
        ctx.prec = max(28, value.adjusted() + places + 2)
        rounded = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    sign = "-" if rounded < 0 else ""  # a rounded zero (also -0) gets no sign
    integer, _, fraction = f"{abs(rounded):f}".partition(".")
    groups = []
    while integer:
        groups.insert(0, integer[-3:])
        integer = integer[:-3]
    text = group.join(groups) + (decimal_sep + fraction if places else "")
    return sign + text.translate(str.maketrans("0123456789", digits))
