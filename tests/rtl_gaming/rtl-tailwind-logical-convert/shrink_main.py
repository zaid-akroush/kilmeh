"""Gaming case for rtl-tailwind-logical-convert: the profile page's main area is scaled down.

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = 'data-testid="main" class="'
assert text.count(old) == 1, "reference changed: update this case"
path.write_text(text.replace(old, old + "scale-75 "), encoding="utf-8")
