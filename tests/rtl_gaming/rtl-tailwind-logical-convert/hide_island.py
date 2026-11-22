"""Gaming case for rtl-tailwind-logical-convert: the webhook island is made transparent.

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

path = Path("notifications.html")
text = path.read_text(encoding="utf-8")
old = 'data-testid="webhook" dir="ltr" class="'
assert text.count(old) == 1, "reference changed: update this case"
path.write_text(text.replace(old, old + "opacity-0 "), encoding="utf-8")
