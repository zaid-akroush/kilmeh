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
        "left-0": "rtl:inset-[0_0_0_auto] ltr:inset-[0_auto_0_0]",
        "border-r": "border-e",
        "ml-64": "rtl:[margin:0_16rem_0_0] ltr:[margin:0_0_0_16rem]",
        "pl-6": "ps-6",
        "rounded-l-lg": "rounded-s-lg",
        "border-l-4": "border-s-4",
        "text-left": "text-start",
        "right-2": "end-2",
    },
)
save(t)
