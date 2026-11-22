"""Mutation for rtl-bidi-chat-feed: message m4 (Arabic first, two names) is fixed left to right.

Runs in the app directory on top of the reference solution.
"""

import re
from pathlib import Path

html = Path("index.html")
text, n = re.subn(
    r'(data-testid="m4">.*?<p class="text") dir="auto"', r'\1 dir="ltr"', html.read_text("utf-8")
)
assert n == 1
html.write_text(text, encoding="utf-8")
