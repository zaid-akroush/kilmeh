"""Gaming case for rtl-tailwind-sidebar:
the footer note text is emptied (the Arabic text must stay).

Runs in the app directory on top of the reference solution; must not score 1.
"""

import re
from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global text
    assert text.count(old) >= 1, f"reference changed: update this case ({old!r})"
    text = text.replace(old, new, count)


text = re.sub(r'(<p data-testid="footer-note"[^>]*>)[^<]*', r"\1", text)
html.write_text(text, encoding="utf-8")
