"""Gaming case for rtl-tailwind-logical-convert: in the Arabic page only, the page title is forced
left-to-right with `direction: ltr; text-align: right` in src/input.css. Its box, padding and
resolved text-align still mirror, so in rtl_mirrors_ltr only the computed-direction rule catches
it; no_physical_css also flags the physical text-align (QA, PR 57).

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

with Path("src/input.css").open("a", encoding="utf-8") as f:
    f.write('[dir=rtl] [data-testid="page-title"]{direction:ltr;text-align:right}\n')
