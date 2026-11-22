"""Mutation for rtl-tailwind-logical-convert (index.html): the tip's corner radii are dropped
(rounded-ss-lg rounded-ee-md removed). No box moves.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = 'data-testid="tip" class="mt-6 rounded-ss-lg rounded-ee-md '
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(text.replace(old, 'data-testid="tip" class="mt-6 '), encoding="utf-8")
