"""Alternative for rtl-bidi-data-cells: each value's text is wrapped in LRI ... PDI
(U+2066, U+2069), as a template helper would emit.

Runs in the app directory on the untouched fixture.
"""

import re
from pathlib import Path

html = Path("index.html")
text, n = re.subn(
    r'(data-testid="(?:path|version|phone|fn)">)(.*?)(</)',
    "\\1\u2066\\2\u2069\\3",
    html.read_text(encoding="utf-8"),
)
assert n == 4
html.write_text(text, encoding="utf-8")
