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
save(t)
css = "[dir=rtl] [data-testid=sidebar]{right:0}[dir=ltr] [data-testid=sidebar]{left:0}[dir=rtl] [data-testid=main]{margin-right:16rem}[dir=ltr] [data-testid=main]{margin-left:16rem}[dir=rtl] [data-testid=badge]{left:.5rem;right:auto}[dir=ltr] [data-testid=badge]{right:.5rem;left:auto}"  # noqa: E501
Path("src/input.css").write_text(
    '@import url("data:text/css,' + css.replace(" ", "%20") + '");\n@import "tailwindcss";\n',
    encoding="utf-8",
)
