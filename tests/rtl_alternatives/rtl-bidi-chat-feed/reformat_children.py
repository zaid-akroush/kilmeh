"""Alternative for rtl-bidi-chat-feed (QA): the reference fix, with each message's author and
text on their own indented lines (whitespace that never renders).

Runs in the app directory on the untouched fixture.
"""

import re
from pathlib import Path

html = Path("index.html")
text, n = re.subn(
    r'(<li class="msg" data-testid="m[0-9]">)(<span class="author">.*?</span>)'
    r'<p class="text">(.*?)</p></li>',
    r'\1\n        \2\n        <p class="text" dir="auto">\3</p>\n      </li>',
    html.read_text(encoding="utf-8"),
)
assert n == 5
html.write_text(text, encoding="utf-8")

css = Path("styles.css")
styles = css.read_text(encoding="utf-8")
old = "  direction: ltr;\n  unicode-bidi: bidi-override;\n"
assert styles.count(old) == 1
css.write_text(styles.replace(old, ""), encoding="utf-8")
