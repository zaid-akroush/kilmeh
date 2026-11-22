"""Alternative for rtl-bidi-chat-feed: a fixed dir per message, as a server that detects the
direction would render it (rtl for Arabic-first, ltr for English- or link-first).

Runs in the app directory on the untouched fixture.
"""

import re
from pathlib import Path

DIRS = {"m1": "rtl", "m2": "ltr", "m3": "ltr", "m4": "rtl", "m5": "rtl"}

html = Path("index.html")
text = html.read_text(encoding="utf-8")
for msg, direction in DIRS.items():
    text, n = re.subn(rf'(data-testid="{msg}">.*?<p class="text")', rf'\1 dir="{direction}"', text)
    assert n == 1, msg
html.write_text(text, encoding="utf-8")

css = Path("styles.css")
styles = css.read_text(encoding="utf-8")
old = "  direction: ltr;\n  unicode-bidi: bidi-override;\n"
assert styles.count(old) == 1
css.write_text(styles.replace(old, ""), encoding="utf-8")
