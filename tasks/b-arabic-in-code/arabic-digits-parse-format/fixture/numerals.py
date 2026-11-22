"""Parse and format numbers written in Western, Arabic-Indic or Extended Arabic-Indic digits.

Digit systems:
  latn     0-9 (U+0030-U+0039), grouping ",", decimal "."
  arab     U+0660-U+0669, grouping U+066C, decimal U+066B (parse also accepts ".")
  arabext  U+06F0-U+06F9, grouping U+066C, decimal U+066B (parse also accepts ".")
"""

from decimal import Decimal


def parse_number(text: str) -> Decimal:
    """Parse a number written in exactly one digit system. Raise ValueError otherwise."""
    raise NotImplementedError


def format_number(value, system: str, places: int = 0) -> str:
    """Format an int or Decimal in the given system with exactly `places` decimals."""
    raise NotImplementedError
