"""Mutation for rtl-tailwind-logical-convert (notifications.html): the title's bottom margin grows (mb-6 to mb-8), moving everything below it in both directions.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("notifications.html")
text = path.read_text(encoding="utf-8")
old = 'data-testid="page-title" class="mb-6 '
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(text.replace(old, 'data-testid="page-title" class="mb-8 '), encoding="utf-8")
