"""Mutation for rtl-tailwind-logical-convert (index.html): one graded element uses rtl:/ltr: logical variants that do not mirror (LTR unchanged).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = 'data-testid="save" class="ms-auto '
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(
    text.replace(old, 'data-testid="save" class="ltr:ms-auto rtl:me-auto '), encoding="utf-8"
)
