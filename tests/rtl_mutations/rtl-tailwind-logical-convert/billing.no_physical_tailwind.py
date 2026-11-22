"""Mutation for rtl-tailwind-logical-convert (billing.html): a harmless physical class (ml-0, a lone zero the CSS check allows) on the title.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("billing.html")
text = path.read_text(encoding="utf-8")
old = 'data-testid="page-title" class="'
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(text.replace(old, 'data-testid="page-title" class="ml-0 '), encoding="utf-8")
