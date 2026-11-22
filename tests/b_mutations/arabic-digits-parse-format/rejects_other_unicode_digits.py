"""Mutation for arabic-digits-parse-format: Devanagari digits are accepted.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

Path("numerals.py").open("a", encoding="utf-8").write("""

_mutated_parse = parse_number


def parse_number(text):
    if text and all("\\u0966" <= c <= "\\u096f" for c in text):
        return Decimal("".join(str(ord(c) - 0x0966) for c in text))
    return _mutated_parse(text)
""")
