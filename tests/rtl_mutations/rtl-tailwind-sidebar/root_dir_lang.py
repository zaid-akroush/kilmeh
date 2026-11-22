"""Mutation for rtl-tailwind-sidebar: html lang goes back to en (dir stays rtl).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = 'lang="ar-JO"'
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(text.replace(old, 'lang="en"'), encoding="utf-8")
