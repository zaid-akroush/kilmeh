"""Gaming case for rtl-tailwind-sidebar:
the whole page is shrunk with a transform, so a 400px card fits at 360px.

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global text
    assert text.count(old) >= 1, f"reference changed: update this case ({old!r})"
    text = text.replace(old, new, count)


sub('data-testid="card" class="relative ', 'data-testid="card" class="min-w-[400px] relative ')
sub('<body class="', '<body class="origin-top-right scale-50 ')
html.write_text(text, encoding="utf-8")
