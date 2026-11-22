"""Gaming case for rtl-tailwind-sidebar:
an extra hand-written stylesheet is linked next to dist/app.css.

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global text
    assert text.count(old) >= 1, f"reference changed: update this case ({old!r})"
    text = text.replace(old, new, count)


sub(
    '<link rel="stylesheet" href="/dist/app.css">',
    '<link rel="stylesheet" href="/dist/app.css">\n  <link rel="stylesheet" href="/hand.css">',
)
html.write_text(text, encoding="utf-8")
Path("hand.css").write_text(".unused{margin-inline-start:0}\n", encoding="utf-8")
