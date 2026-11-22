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
        "left-0": "ltr:left-0 rtl:start-0",
        "border-r": "ltr:border-r rtl:border-e",
        "ml-64": "ltr:ml-64 rtl:ms-64",
        "pl-6": "ltr:pl-6 rtl:ps-6",
        "rounded-l-lg": "ltr:rounded-l-lg rtl:rounded-s-lg",
        "border-l-4": "ltr:border-l-4 rtl:border-s-4",
        "text-left": "ltr:text-left rtl:text-start",
        "right-2": "ltr:right-2 rtl:end-2",
    },
)
save(t)
