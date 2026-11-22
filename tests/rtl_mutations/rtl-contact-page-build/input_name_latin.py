"""Mutation for rtl-contact-page-build: name field forced rtl.

Runs in the app directory on top of the reference solution.
"""

import re
from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
new, n = re.subn('(<input[^>]*data-testid="name"[^>]*?) dir="auto"', '\\1 dir="rtl"', text, count=1)
assert n == 1, "reference changed: update this mutation"
path.write_text(new, encoding="utf-8")
