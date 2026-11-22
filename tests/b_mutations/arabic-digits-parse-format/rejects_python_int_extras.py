"""Mutation for arabic-digits-parse-format: a leading "+" is accepted, as int() does.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

Path("numerals.py").open("a", encoding="utf-8").write("""

_mutated_parse = parse_number


def parse_number(text):
    if text.startswith("+"):
        return _mutated_parse(text[1:])
    return _mutated_parse(text)
""")
