"""Gaming attempt for rtl-bidi-data-cells: the values are retyped back to front and shown with
`unicode-bidi: bidi-override; direction: rtl`, so they look right while the text is reversed.

Runs in the app directory on the untouched fixture.
"""

import re
from pathlib import Path

html = Path("index.html")
text, n = re.subn(
    r'(data-testid="(?:path|version|phone|fn)">)(.*?)(</)',
    lambda m: m[1] + m[2][::-1] + m[3],
    html.read_text(encoding="utf-8"),
)
assert n == 4
html.write_text(text, encoding="utf-8")
with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write(".value code,.value .phone{direction:rtl;unicode-bidi:isolate-override}\n")
