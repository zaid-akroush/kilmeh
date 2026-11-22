"""Gaming case for rtl-tailwind-logical-convert: the active nav link's accent colour is dropped
(border-s-blue-500 removed) on the billing page. No box moves.

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

path = Path("billing.html")
text = path.read_text(encoding="utf-8")
old = " border-s-blue-500 "
assert text.count(old) == 1, "reference changed: update this case"
path.write_text(text.replace(old, " "), encoding="utf-8")
