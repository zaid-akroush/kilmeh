"""Alternative for rtl-bidi-name-slots: each value is wrapped in FSI ... PDI (U+2068, U+2069),
as a server-side template helper would do.

Runs in the app directory on the untouched fixture.
"""

import re
from pathlib import Path

html = Path("index.html")
text, n = re.subn(
    r'(<span class="slot" data-testid="\w+">)(.*?)(</span>)',
    "\\1\u2068\\2\u2069\\3",
    html.read_text(encoding="utf-8"),
)
assert n == 4
html.write_text(text, encoding="utf-8")
