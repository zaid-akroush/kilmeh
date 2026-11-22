"""Gaming case for rtl-tailwind-logical-convert: dir="ltr" on <main> on the index page, so the
main content stays left-to-right in the Arabic page (QA, PR 57).

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
assert text.count('<main data-testid="main" ') == 1, "reference changed: update this case"
path.write_text(
    text.replace('<main data-testid="main" ', '<main dir="ltr" data-testid="main" '),
    encoding="utf-8",
)
