"""Known-bad solution (the naive fix): runs in the app directory (the current directory).

Sets dir="rtl" and swaps every left for right. The geometry looks right in RTL, but the page
does not follow <html dir>, and the classes are still physical.
"""

import re
from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
assert text.count('<html lang="en">') == 1
text = text.replace('<html lang="en">', '<html dir="rtl" lang="ar-JO">')

SWAP = {
    "left-0": "right-0",
    "border-r": "border-l",
    "ml-64": "mr-64",
    "pl-6": "pr-6",
    "rounded-l-lg": "rounded-r-lg",
    "border-l-4": "border-r-4",
    "text-left": "text-right",
    "right-2": "left-2",
}


def fix(match):
    tokens = [SWAP.get(t, t) for t in match.group(1).split()]
    return 'class="' + " ".join(tokens) + '"'


text = re.sub(r'class="([^"]*)"', fix, text)
path.write_text(text, encoding="utf-8")
