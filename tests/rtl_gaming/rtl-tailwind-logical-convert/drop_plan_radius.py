"""Gaming case for rtl-tailwind-logical-convert: the plan card's corner radii are dropped
(rounded-ss-lg rounded-ee-md removed) on the billing page. No box moves.

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

path = Path("billing.html")
text = path.read_text(encoding="utf-8")
old = 'data-testid="plan" class="relative rounded-ss-lg rounded-ee-md '
assert text.count(old) == 1, "reference changed: update this case"
path.write_text(text.replace(old, 'data-testid="plan" class="relative '), encoding="utf-8")
