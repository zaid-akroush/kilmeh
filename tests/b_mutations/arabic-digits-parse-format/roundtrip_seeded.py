"""Mutation for arabic-digits-parse-format: values of 10^10 or more go through float.

Runs in the app directory on top of the reference solution. The fixed format cases and the
invoice totals stay below 10^10; only the seeded round trip reaches that range.
"""

from pathlib import Path

Path("numerals.py").open("a", encoding="utf-8").write("""

_mutated_format = format_number


def format_number(value, system, places=0):
    if abs(value) >= 10**10:
        value = Decimal(float(value))
    return _mutated_format(value, system, places)
""")
