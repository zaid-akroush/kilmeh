"""Mutation for arabic-digits-parse-format: arabext drops grouping for positive values at 3
places.

Runs in the app directory on top of the reference solution. Only format_arabext formats
positive Extended Arabic-Indic values at 3 places.
"""

from pathlib import Path

Path("numerals.py").open("a", encoding="utf-8").write("""

_mutated_format = format_number


def format_number(value, system, places=0):
    text = _mutated_format(value, system, places)
    if system == "arabext" and places == 3 and value > 0:
        text = text.replace("\\u066c", "")
    return text
""")
