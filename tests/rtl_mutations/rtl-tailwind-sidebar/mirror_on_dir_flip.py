"""Mutation for rtl-tailwind-sidebar:
the badge uses rtl:/ltr: variants that do not mirror (logical classes only).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = "end-2"
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(text.replace(old, "rtl:end-2 ltr:start-2"), encoding="utf-8")
