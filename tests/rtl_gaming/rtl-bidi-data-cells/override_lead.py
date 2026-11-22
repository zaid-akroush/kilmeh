"""Gaming attempt for rtl-bidi-data-cells (QA repro): the opening Arabic words of the code cell
are wrapped in a left-to-right bidi-override span, which reverses their letters.

Runs in the app directory on top of the reference.
"""

import re
from pathlib import Path

html = Path("index.html")
text, n = re.subn(
    r'(data-testid="r-code">.*?<td class="value">)([^<]*?)(<code)',
    r'\1<span style="unicode-bidi:bidi-override;direction:ltr">\2</span>\3',
    html.read_text(encoding="utf-8"),
)
assert n == 1
html.write_text(text, encoding="utf-8")
