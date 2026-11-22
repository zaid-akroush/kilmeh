"""Mutation for rtl-tailwind-sidebar: a harmless physical class (ml-0) is added to the footer note.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = "mt-6 text-sm"
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(text.replace(old, "mt-6 ml-0 text-sm"), encoding="utf-8")
