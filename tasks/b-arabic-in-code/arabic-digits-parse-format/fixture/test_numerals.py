"""Six examples. Run with `python3 test_numerals.py` (pytest is not installed).

Non-ASCII characters are written as escapes so every code point is visible.
"""

from decimal import Decimal

from numerals import format_number, parse_number

# Arabic-Indic 123
assert parse_number("\u0661\u0662\u0663") == Decimal("123")
# Extended Arabic-Indic 1,234.5 with U+066C grouping and U+066B decimal separator
assert parse_number("\u06f1\u066c\u06f2\u06f3\u06f4\u066b\u06f5") == Decimal("1234.5")
assert parse_number("1,234.5") == Decimal("1234.5")

# Western 1 then Arabic-Indic 2 and 3: mixed systems are rejected
try:
    parse_number("1\u0662\u0663")
except ValueError:
    pass
else:
    raise AssertionError("mixed digit systems must raise ValueError")

# Arabic-Indic 1,234.50
assert format_number(Decimal("1234.5"), "arab", 2) == "\u0661\u066c\u0662\u0663\u0664\u066b\u0665\u0660"
assert format_number(-7, "latn") == "-7"

print("6 examples pass")
