"""Mutation for arabic-digits-parse-format: Arabic-Indic and Extended digits may be mixed.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

Path("numerals.py").open("a", encoding="utf-8").write("""

_mutated_parse = parse_number


def parse_number(text):
    arab = [c for c in text if "\\u0660" <= c <= "\\u0669"]
    ext = [c for c in text if "\\u06f0" <= c <= "\\u06f9"]
    if arab and ext and len(arab) + len(ext) == len(text):
        return Decimal("".join(str(ord(c) % 16) for c in text))
    return _mutated_parse(text)
""")
