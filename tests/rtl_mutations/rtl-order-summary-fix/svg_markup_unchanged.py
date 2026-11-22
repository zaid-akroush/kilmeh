"""Mutation for rtl-order-summary-fix: an icon's SVG markup is edited.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = 'data-testid="back-icon"'
assert old in text, "reference changed: update this mutation"
path.write_text(text.replace(old, old + ' data-x="1"', 1), encoding="utf-8")
