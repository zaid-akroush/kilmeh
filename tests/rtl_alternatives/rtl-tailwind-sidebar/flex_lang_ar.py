"""Alternative correct solution: a flex row with a sticky sidebar, and lang="ar".

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


apply(
    {
        **LOGICAL,
        "bg-slate-50": "bg-slate-50 flex",
        "fixed": "sticky",
        "left-0": "",
        "w-64": "w-64 shrink-0",
        "h-full": "h-screen",
        "ml-64": "min-w-0 flex-1",
    },
    lang="ar",
)
