"""Mutation for arabic-digits-parse-format: Western input with leading spaces is rejected.

Runs in the app directory on top of the reference solution. Only parse_latn uses padded
Western input.
"""

from pathlib import Path

Path("numerals.py").open("a", encoding="utf-8").write("""

_mutated_parse = parse_number


def parse_number(text):
    if text.startswith(" ") and any(c in "0123456789" for c in text):
        raise ValueError("mutation: leading spaces not stripped")
    return _mutated_parse(text)
""")
