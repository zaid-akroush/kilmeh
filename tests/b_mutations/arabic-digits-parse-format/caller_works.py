"""Mutation for arabic-digits-parse-format: invoice.py formats totals with 3 places.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("invoice.py")
text = path.read_text(encoding="utf-8")
assert "format_number(total, system, 2)" in text, "fixture changed: update this mutation"
path.write_text(text.replace("format_number(total, system, 2)", "format_number(total, system, 3)"))
