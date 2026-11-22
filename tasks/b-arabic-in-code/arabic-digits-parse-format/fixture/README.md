# numerals

Parse and format numbers in three digit systems: Western (`latn`), Arabic-Indic (`arab`, U+0660 to U+0669) and Extended Arabic-Indic (`arabext`, U+06F0 to U+06F9).

- `numerals.py`: `parse_number(text)` and `format_number(value, system, places=0)` (stubs).
- `invoice.py`: `total_text(amounts, system)` sums amounts and formats the total with 2 decimals.
- `test_numerals.py`: six examples, `python3 test_numerals.py`.

Standard library only.
