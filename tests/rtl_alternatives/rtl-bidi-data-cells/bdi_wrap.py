"""Alternative for rtl-bidi-data-cells: each value's text is wrapped in <bdi dir="ltr">.

Runs in the app directory on the untouched fixture.
"""

import re
from pathlib import Path

html = Path("index.html")
text, n = re.subn(
    r'(data-testid="(?:path|version|phone|fn)">)(.*?)(</)',
    r'\1<bdi dir="ltr">\2</bdi>\3',
    html.read_text(encoding="utf-8"),
)
assert n == 4
html.write_text(text, encoding="utf-8")
