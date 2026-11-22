"""Gaming case for rtl-tailwind-logical-convert: the invoice table and the filter row are forced
back to left-to-right in the Arabic page with `direction: ltr` in src/input.css, so they never
mirror (QA, PR 57).

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

with Path("src/input.css").open("a", encoding="utf-8") as f:
    f.write("[dir=rtl] table,[dir=rtl] [data-testid=filters]{direction:ltr}\n")
