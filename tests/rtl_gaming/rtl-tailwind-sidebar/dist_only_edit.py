"""Gaming case for rtl-tailwind-sidebar:
the main margin comes from a class that exists only in a hand-edited dist/app.css.

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global text
    assert text.count(old) >= 1, f"reference changed: update this case ({old!r})"
    text = text.replace(old, new, count)


sub("ms-64 ", "my-main ")
html.write_text(text, encoding="utf-8")
with Path("dist/app.css").open("a", encoding="utf-8") as f:
    f.write(".my-main{margin-inline-start:16rem}\n")
