"""Mutation for rtl-tailwind-sidebar: the footer note loses its data-testid.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = ' data-testid="footer-note"'
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(text.replace(old, ""), encoding="utf-8")
