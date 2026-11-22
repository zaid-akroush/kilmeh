"""Reference solution: every slot becomes a <bdi> (isolated, direction from its own text).

Runs in the app directory.
"""

import re
from pathlib import Path

html = Path("index.html")
text, n = re.subn(
    r'<span class="slot"( data-testid="\w+">.*?)</span>',
    r'<bdi class="slot"\1</bdi>',
    html.read_text(encoding="utf-8"),
)
assert n == 4
html.write_text(text, encoding="utf-8")
