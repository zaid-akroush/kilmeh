"""Gaming attempt for rtl-contact-page-build: move data-part=head to a different shape instead of flipping.

Runs on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = '<g data-part="head"><polyline points="12,4 18,10 12,16" fill="none" '
assert old in text
text = text.replace(old, '<g data-part="head"><polyline points="8,4 2,10 8,16" fill="none" ', 1)
path.write_text(text, encoding="utf-8")
