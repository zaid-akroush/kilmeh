"""Alternative correct solution for rtl-tailwind-sidebar: hand-written logical CSS in input.css.

The sidebar and main layout move into component classes in `src/input.css` that use CSS logical
properties (`inset-inline-start`, `border-inline-end`, `margin-inline-start`), and the cards and
badge use Tailwind arbitrary properties. No `start-*`, `ms-*` or `end-*` utilities are used.
Runs in the app directory on a fresh copy of the fixture; must score 1.
"""

import re
from pathlib import Path

CSS = """@import "tailwindcss";

@layer components {
  .sidebar {
    position: fixed;
    inset-block: 0;
    inset-inline-start: 0;
    width: 16rem;
    border-inline-end: 1px solid var(--color-slate-200);
  }
  .content {
    margin-inline-start: 16rem;
    padding-inline-start: 1.5rem;
  }
}
"""
Path("src/input.css").write_text(CSS, encoding="utf-8")

path = Path("index.html")
text = path.read_text(encoding="utf-8")
assert text.count('<html lang="en">') == 1
text = text.replace('<html lang="en">', '<html dir="rtl" lang="ar-JO">')

SWAP = {
    "fixed": "sidebar",
    "left-0": "",
    "top-0": "",
    "h-full": "",
    "w-64": "",
    "border-r": "",
    "border-slate-200": "",
    "ml-64": "content",
    "pl-6": "",
    "rounded-l-lg": "[border-start-start-radius:0.5rem] [border-end-start-radius:0.5rem]",
    "border-l-4": "[border-inline-start:4px_solid_var(--color-blue-500)]",
    "border-blue-500": "",
    "text-left": "[text-align:start]",
    "right-2": "[inset-inline-end:0.5rem]",
}


def fix(match):
    tokens = " ".join(SWAP.get(t, t) for t in match.group(1).split()).split()
    return 'class="' + " ".join(tokens) + '"'


text = re.sub(r'class="([^"]*)"', fix, text)
path.write_text(text, encoding="utf-8")
