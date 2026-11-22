"""Alternative for rtl-bidi-chat-feed (QA): `<p dir="auto">` with the message text on its own
indented line inside the paragraph.

Runs in the app directory on the untouched fixture.
"""

import re
from pathlib import Path

html = Path("index.html")
text, n = re.subn(
    r'<p class="text">(.*?)</p>',
    r'<p class="text" dir="auto">\n          \1\n        </p>',
    html.read_text(encoding="utf-8"),
)
assert n == 5
html.write_text(text, encoding="utf-8")

css = Path("styles.css")
styles = css.read_text(encoding="utf-8")
old = "  direction: ltr;\n  unicode-bidi: bidi-override;\n"
assert styles.count(old) == 1
css.write_text(styles.replace(old, ""), encoding="utf-8")
