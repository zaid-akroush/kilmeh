"""Mutation for rtl-nav-fix: html lang goes back to en (dir stays rtl).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
assert 'lang="ar-JO"' in text, "reference changed: update this mutation"
path.write_text(text.replace('lang="ar-JO"', 'lang="en"', 1), encoding="utf-8")
