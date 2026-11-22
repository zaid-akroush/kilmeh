"""Alternative correct solution for rtl-tailwind-sidebar: a CSS grid instead of fixed positioning.

The body becomes a two-column grid (16rem sidebar, rest for main) and the sidebar is sticky, so
there is no `start-*` and no margin on main: the grid follows <html dir> by itself. Runs in the
app directory on a fresh copy of the fixture; must score 1.
"""

import re
from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
assert text.count('<html lang="en">') == 1
text = text.replace('<html lang="en">', '<html dir="rtl" lang="ar-JO">')

SWAP = {
    "fixed": "sticky",
    "left-0": "",
    "w-64": "",
    "h-full": "h-screen",
    "border-r": "border-e",
    "ml-64": "",
    "pl-6": "ps-6",
    "rounded-l-lg": "rounded-s-lg",
    "border-l-4": "border-s-4",
    "text-left": "text-start",
    "right-2": "end-2",
    "bg-slate-50": "bg-slate-50 grid min-h-screen grid-cols-[16rem_minmax(0,1fr)]",
}


def fix(match):
    tokens = " ".join(SWAP.get(t, t) for t in match.group(1).split()).split()
    return 'class="' + " ".join(tokens) + '"'


text = re.sub(r'class="([^"]*)"', fix, text)
path.write_text(text, encoding="utf-8")
