"""Gaming case for rtl-tailwind-logical-convert: rtl: variants put the tip's accent border,
padding and text alignment back on the LTR side in the Arabic page (logical classes only, so
nothing physical is compiled), and the LTR page is unchanged (QA, PR 57).

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = 'data-testid="tip" class="'
assert text.count(old) == 1, "reference changed: update this case"
new = old + "rtl:border-s-0 rtl:border-e-4 rtl:pe-5 rtl:text-end "
path.write_text(text.replace(old, new), encoding="utf-8")
