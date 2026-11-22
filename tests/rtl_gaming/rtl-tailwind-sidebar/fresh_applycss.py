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
        "left-0": "sb",
        "border-r": "",
        "ml-64": "mn",
        "pl-6": "",
        "rounded-l-lg": "",
        "border-l-4": "",
        "text-left": "",
        "right-2": "bd",
    },
)
save(t)
Path("src/input.css").write_text(
    """@import "tailwindcss";
@layer components {
  [dir=rtl] .sb { @apply right-0 border-l; }
  [dir=ltr] .sb { @apply left-0 border-r; }
  [dir=rtl] .mn { @apply mr-64 pr-6; }
  [dir=ltr] .mn { @apply ml-64 pl-6; }
  [dir=rtl] .bd { @apply left-2; }
  [dir=ltr] .bd { @apply right-2; }
}
""",
    encoding="utf-8",
)
