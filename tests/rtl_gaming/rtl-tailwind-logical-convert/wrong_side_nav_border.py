"""Gaming case for rtl-tailwind-logical-convert: the inactive nav links get their accent border
on the wrong side (border-e-4 in place of border-s-4) on the profile page. No box moves.

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = "border-s-4 border-s-transparent py-2 ps-3 hover:border-s-slate-300"
assert text.count(old) == 2, "reference changed: update this case"
new = "border-e-4 border-e-transparent py-2 ps-3 hover:border-e-slate-300"
path.write_text(text.replace(old, new), encoding="utf-8")
