"""Reference solution: runs in the app directory (the current directory)."""

import re
from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
assert text.count('<html lang="en">') == 1
text = text.replace('<html lang="en">', '<html dir="rtl" lang="ar-JO">')

SWAP = {
    "left-0": "start-0",
    "border-r": "border-e",
    "ml-64": "ms-64",
    "pl-6": "ps-6",
    "rounded-l-lg": "rounded-s-lg",
    "border-l-4": "border-s-4",
    "text-left": "text-start",
    "right-2": "end-2",
}


def fix(match):
    tokens = [SWAP.get(t, t) for t in match.group(1).split()]
    return 'class="' + " ".join(tokens) + '"'


text = re.sub(r'class="([^"]*)"', fix, text)
path.write_text(text, encoding="utf-8")
