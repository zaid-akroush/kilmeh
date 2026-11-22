"""Mutation for rtl-tailwind-logical-convert (billing.html): the title is 400px wide below the md breakpoint (nothing changes at 1280px).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("billing.html")
text = path.read_text(encoding="utf-8")
old = 'data-testid="page-title" class="'
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(
    text.replace(old, 'data-testid="page-title" class="max-md:w-[400px] '), encoding="utf-8"
)
