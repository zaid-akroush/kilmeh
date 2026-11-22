"""Alternative correct solution: the stylesheet is linked with a relative href.

Runs in the app directory on a fresh copy of the fixture; must score 1.
"""

import re
from pathlib import Path

LOGICAL = {
    "left-0": "start-0",
    "border-r": "border-e",
    "ml-64": "ms-64",
    "pl-6": "ps-6",
    "rounded-l-lg": "rounded-s-lg",
    "border-l-4": "border-s-4",
    "text-left": "text-start",
    "right-2": "end-2",
}


def apply(mapping, lang="ar-JO"):
    path = Path("index.html")
    text = path.read_text(encoding="utf-8")
    assert text.count('<html lang="en">') == 1
    text = text.replace('<html lang="en">', f'<html dir="rtl" lang="{lang}">')

    def fix(match):
        tokens = " ".join(mapping.get(t, t) for t in match.group(1).split()).split()
        return 'class="' + " ".join(tokens) + '"'

    path.write_text(re.sub(r'class="([^"]*)"', fix, text), encoding="utf-8")


apply(LOGICAL)
page = Path("index.html")
text = page.read_text(encoding="utf-8")
assert text.count('href="/dist/app.css"') == 1
page.write_text(text.replace('href="/dist/app.css"', 'href="dist/app.css"'), encoding="utf-8")
