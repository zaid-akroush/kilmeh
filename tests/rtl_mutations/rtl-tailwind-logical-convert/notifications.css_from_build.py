"""Mutation for rtl-tailwind-logical-convert (notifications.html): an inline style attribute (a colour, no physical property) on the title.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("notifications.html")
text = path.read_text(encoding="utf-8")
old = 'data-testid="page-title" class="'
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(
    text.replace(old, 'data-testid="page-title" style="color: #0f172a" class="'), encoding="utf-8"
)
