"""Mutation for arabic-digits-parse-format: Arabic-Indic input with leading spaces is rejected.

Runs in the app directory on top of the reference solution. Only parse_arab uses padded
Arabic-Indic input.
"""

from pathlib import Path

Path("numerals.py").open("a", encoding="utf-8").write("""

_mutated_parse = parse_number


def parse_number(text):
    if text.startswith(" ") and any("\\u0660" <= c <= "\\u0669" for c in text):
        raise ValueError("mutation: leading spaces not stripped")
    return _mutated_parse(text)
""")
