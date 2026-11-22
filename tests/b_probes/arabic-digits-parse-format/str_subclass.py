"""Probe: format_number returns a str subclass with the right text. The prompt requires exactly
str, so every check that reads format_number output must fail.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

Path("numerals.py").open("a", encoding="utf-8").write("""

class _SubStr(str):
    pass


_exact_format = format_number


def format_number(value, system, places=0):
    return _SubStr(_exact_format(value, system, places))
""")
