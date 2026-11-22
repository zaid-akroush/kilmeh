"""Mutation for arabic-digits-parse-format: rounds half up instead of half to even.

Runs in the app directory on top of the reference solution. Only format_negative_and_rounding
has exact ties.
"""

from pathlib import Path

Path("numerals.py").open("a", encoding="utf-8").write("""

_mutated_format = format_number


def format_number(value, system, places=0):
    from decimal import ROUND_HALF_UP

    rounded = Decimal(value).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    return _mutated_format(rounded, system, places)
""")
