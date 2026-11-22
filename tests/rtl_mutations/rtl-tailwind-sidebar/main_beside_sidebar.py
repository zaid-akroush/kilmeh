"""Mutation for rtl-tailwind-sidebar:
the main content loses its start margin and sits under the sidebar.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = "ms-64 "
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(text.replace(old, ""), encoding="utf-8")
