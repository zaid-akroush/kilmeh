"""Gaming case for rtl-tailwind-logical-convert: the IBAN island (a hard element) is deleted.

Runs in the app directory on top of the reference solution; must not score 1.
"""

import re
from pathlib import Path

path = Path("billing.html")
text = path.read_text(encoding="utf-8")
text, n = re.subn(r'\s*<p data-testid="iban"[^>]*>[^<]*</p>', "", text)
assert n == 1, "reference changed: update this case"
path.write_text(text, encoding="utf-8")
