"""Mutation for rtl-bidi-chat-feed: message m2 (English first) is fixed right to left.

Runs in the app directory on top of the reference solution.
"""

import re
from pathlib import Path

html = Path("index.html")
text, n = re.subn(
    r'(data-testid="m2">.*?<p class="text") dir="auto"', r'\1 dir="rtl"', html.read_text("utf-8")
)
assert n == 1
html.write_text(text, encoding="utf-8")
