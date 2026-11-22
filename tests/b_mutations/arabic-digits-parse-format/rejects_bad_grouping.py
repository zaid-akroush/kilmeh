"""Mutation for arabic-digits-parse-format: Western groups of two digits are accepted.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

Path("numerals.py").open("a", encoding="utf-8").write("""

_mutated_parse = parse_number


def parse_number(text):
    if re.fullmatch(r"[0-9]{1,3}(?:,[0-9]{2,3})+", text):
        return Decimal(text.replace(",", ""))
    return _mutated_parse(text)
""")
