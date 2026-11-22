"""Gaming case from QA (PR 30), run on a fresh fixture; must not score 1."""

import re
from pathlib import Path


def load():
    return Path("index.html").read_text(encoding="utf-8")


def head(t, lang="ar-JO", dir_="rtl"):
    assert t.count('<html lang="en">') == 1
    return t.replace('<html lang="en">', f'<html dir="{dir_}" lang="{lang}">')


def swap(t, mp):
    def fix(m):
        toks = " ".join(mp.get(x, x) for x in m.group(1).split()).split()
        return 'class="' + " ".join(toks) + '"'

    return re.sub(r'class="([^"]*)"', fix, t)


def save(t):
    Path("index.html").write_text(t, encoding="utf-8")


t = head(load())
t = swap(
    t,
    {
        "left-0": "",
        "border-r": "",
        "ml-64": "",
        "pl-6": "",
        "rounded-l-lg": "",
        "border-l-4": "",
        "text-left": "",
        "right-2": "",
    },
)
t = t.replace(
    '<aside data-testid="sidebar" class="', '<aside data-testid="sidebar" class="sb '
).replace('<main data-testid="main" class="', '<main data-testid="main" class="mn ')
save(t)
Path("src/input.css").write_text(
    """@import "tailwindcss";
@layer base {
  [dir=rtl] .sb { right:0; border-left-width:1px }
  [dir=ltr] .sb { left:0; border-right-width:1px }
  [dir=rtl] .mn { margin-right:16rem; padding-right:1.5rem }
  [dir=ltr] .mn { margin-left:16rem; padding-left:1.5rem }
  [dir=rtl] [data-testid=badge] { left:.5rem; right:auto }
  [dir=ltr] [data-testid=badge] { right:.5rem; left:auto }
}
""",
    encoding="utf-8",
)
