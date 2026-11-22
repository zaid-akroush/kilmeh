"""Mutation for rtl-tailwind-logical-convert (billing.html): the amount column loses its end
alignment (text-end becomes text-start in the header and both amount cells). No box moves.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("billing.html")
text = path.read_text(encoding="utf-8")
old = "pe-4 text-end"
assert text.count(old) == 3, "reference changed: update this mutation"
path.write_text(text.replace(old, "pe-4 text-start"), encoding="utf-8")
