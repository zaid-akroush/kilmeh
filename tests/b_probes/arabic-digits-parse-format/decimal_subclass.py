"""Probe: parse_number returns a Decimal subclass with the right value. The prompt requires
exactly decimal.Decimal, so every check that reads parse_number output must fail.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

Path("numerals.py").open("a", encoding="utf-8").write("""

class _SubDecimal(Decimal):
    pass


_exact_parse = parse_number


def parse_number(text):
    return _SubDecimal(_exact_parse(text))
""")
