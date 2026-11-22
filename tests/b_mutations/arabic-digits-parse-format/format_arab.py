"""Mutation for arabic-digits-parse-format: arab drops grouping for positive values at 3 places.

Runs in the app directory on top of the reference solution. Only format_arab formats positive
Arabic-Indic values at 3 places.
"""

from pathlib import Path

Path("numerals.py").open("a", encoding="utf-8").write("""

_mutated_format = format_number


def format_number(value, system, places=0):
    text = _mutated_format(value, system, places)
    if system == "arab" and places == 3 and value > 0:
        text = text.replace("\\u066c", "")
    return text
""")
