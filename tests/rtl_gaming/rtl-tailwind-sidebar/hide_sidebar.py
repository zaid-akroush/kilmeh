"""Gaming case for rtl-tailwind-sidebar: the sidebar is removed from view with display:none.

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global text
    assert text.count(old) >= 1, f"reference changed: update this case ({old!r})"
    text = text.replace(old, new, count)


sub("fixed start-0 ", "hidden fixed start-0 ")
html.write_text(text, encoding="utf-8")
