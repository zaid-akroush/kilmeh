"""Mutation for rtl-tailwind-logical-convert (notifications.html): the filter row's scroll padding
is dropped (scroll-ps-4 removed). No box moves.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("notifications.html")
text = path.read_text(encoding="utf-8")
old = " scroll-ps-4 "
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(text.replace(old, " "), encoding="utf-8")
