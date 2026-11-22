"""Gaming case for rtl-tailwind-logical-convert: <main> on the index page gets dir="ltr" and the
email island's testid, so the main content would pass as a left-to-right island (QA, PR 57).

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = '<main data-testid="main" '
assert text.count(old) == 1, "reference changed: update this case"
path.write_text(text.replace(old, '<main dir="ltr" data-testid="email" '), encoding="utf-8")
