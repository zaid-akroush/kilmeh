"""Mutation for rtl-tailwind-sidebar: the first card gets min-w-[400px], which sticks out of a
360px screen (and changes nothing at 1280px).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = 'data-testid="card" class="relative '
assert text.count(old) == 3, "reference changed: update this mutation"
path.write_text(text.replace(old, 'data-testid="card" class="min-w-[400px] relative ', 1), "utf-8")
