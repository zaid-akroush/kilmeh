"""Alternative for rtl-bidi-chat-feed: each message text is wrapped in <bdi> (auto direction)
and the override is dropped.

Runs in the app directory on the untouched fixture.
"""

import re
from pathlib import Path

html = Path("index.html")
text, n = re.subn(
    r'<p class="text">(.*?)</p>', r'<p class="text"><bdi>\1</bdi></p>', html.read_text("utf-8")
)
assert n == 5
html.write_text(text, encoding="utf-8")

css = Path("styles.css")
styles = css.read_text(encoding="utf-8")
old = "  direction: ltr;\n  unicode-bidi: bidi-override;\n"
assert styles.count(old) == 1
css.write_text(styles.replace(old, ""), encoding="utf-8")
