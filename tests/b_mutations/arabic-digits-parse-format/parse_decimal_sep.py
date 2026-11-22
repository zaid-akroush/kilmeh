"""Mutation for arabic-digits-parse-format: "." is no longer accepted with Eastern digits.

Runs in the app directory on top of the reference solution. Only parse_decimal_sep uses "."
with Eastern digits (the formatter writes U+066B, so the round trip is unaffected).
"""

from pathlib import Path

Path("numerals.py").open("a", encoding="utf-8").write("""

_mutated_parse = parse_number


def parse_number(text):
    eastern = any("\\u0660" <= c <= "\\u0669" or "\\u06f0" <= c <= "\\u06f9" for c in text)
    if eastern and "." in text:
        raise ValueError("mutation: '.' rejected with Eastern digits")
    return _mutated_parse(text)
""")
