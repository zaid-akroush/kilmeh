"""Reference solution: runs in the app directory (the current directory).

Converts every physical Tailwind utility on the three pages and the `@apply` in src/input.css to
its logical form, keeping variants (md:, hover:) and values, and sets lang and dir on <html>.
The left-to-right islands keep dir="ltr"; inside them a logical class acts as the old physical one.
"""

import re
from pathlib import Path

# utility prefix -> logical prefix; longest first so `rounded-tl` wins over `rounded-l`
PREFIXES = [
    ("scroll-pl-", "scroll-ps-"),
    ("scroll-pr-", "scroll-pe-"),
    ("rounded-tl", "rounded-ss"),
    ("rounded-tr", "rounded-se"),
    ("rounded-bl", "rounded-es"),
    ("rounded-br", "rounded-ee"),
    ("rounded-l", "rounded-s"),
    ("rounded-r", "rounded-e"),
    ("border-l", "border-s"),
    ("border-r", "border-e"),
    ("text-left", "text-start"),
    ("text-right", "text-end"),
    ("float-left", "float-start"),
    ("float-right", "float-end"),
    ("-ml-", "-ms-"),
    ("-mr-", "-me-"),
    ("ml-", "ms-"),
    ("mr-", "me-"),
    ("pl-", "ps-"),
    ("pr-", "pe-"),
    ("left-", "start-"),
    ("right-", "end-"),
]


def convert(token: str) -> str:
    *variants, utility = token.split(":")
    for old, new in PREFIXES:
        # `rounded-l` must not catch `rounded-lg`: a prefix ends at a dash or the end
        if utility.startswith(old) and (
            old.endswith("-") or len(utility) == len(old) or utility[len(old)] == "-"
        ):
            utility = new + utility[len(old) :]
            break
    return ":".join([*variants, utility])


def fix(match):
    return 'class="' + " ".join(convert(t) for t in match.group(1).split()) + '"'


for name in ("index.html", "notifications.html", "billing.html"):
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    assert text.count('<html lang="en">') == 1
    text = text.replace('<html lang="en">', '<html dir="rtl" lang="ar-JO">')
    path.write_text(re.sub(r'class="([^"]*)"', fix, text), encoding="utf-8")

css = Path("src/input.css")
text = css.read_text(encoding="utf-8")
assert text.count("@apply mr-2;") == 1
css.write_text(text.replace("@apply mr-2;", "@apply me-2;"), encoding="utf-8")
