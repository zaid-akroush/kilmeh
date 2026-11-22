"""Alternative correct solution for rtl-tailwind-logical-convert: restructure where it is simpler.

Logical utilities like the reference, but: the avatar float becomes a flex row with `gap-4`,
the download icon's margin becomes `gap-2` on the button, `inset-s-*` replaces `start-*`, the
`@apply` becomes a hand-written logical property, and the pages use `lang="ar"`.
Runs in the app directory on a fresh copy of the fixture; must score 1.
"""

import re
from pathlib import Path

LOGICAL = {
    "l": "s",
    "r": "e",
}
SIMPLE = {
    "text-left": "text-start",
    "text-right": "text-end",
    "float-right": "float-end",
    "rounded-tl-lg": "rounded-ss-lg",
    "rounded-br-md": "rounded-ee-md",
    "left-0": "inset-s-0",
    "right-3": "inset-e-3",
}


def convert(token):
    *variants, utility = token.split(":")
    if utility in SIMPLE:
        utility = SIMPLE[utility]
    else:
        utility = re.sub(
            r"^(-?(?:scroll-)?[mp]|border|rounded)-?([lr])(?=-|$)",
            lambda m: f"{m[1]}{'-' if m[1] in ('border', 'rounded') else ''}{LOGICAL[m[2]]}",
            utility,
        )
    return ":".join([*variants, utility])


def fix(match):
    tokens = match.group(1).split()
    if "float-left" in tokens:  # the avatar: a flex item now, no float or margin
        tokens = [t for t in tokens if t not in ("float-left", "mr-4")] + ["shrink-0"]
    return 'class="' + " ".join(convert(t) for t in tokens) + '"'


for name in ("index.html", "notifications.html", "billing.html"):
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    assert text.count('<html lang="en">') == 1
    text = text.replace('<html lang="en">', '<html dir="rtl" lang="ar">')
    text = text.replace(
        'data-testid="profile-card" class="flow-root ',
        'data-testid="profile-card" class="flex items-start gap-4 ',
    )
    text = text.replace('<div class="overflow-hidden">', '<div class="min-w-0 flex-1">')
    text = text.replace(
        'class="ml-auto inline-flex items-center ', 'class="ml-auto inline-flex items-center gap-2 '
    )
    text = text.replace('<span class="btn-icon h-3 w-3', '<span class="h-3 w-3')
    path.write_text(re.sub(r'class="([^"]*)"', fix, text), encoding="utf-8")

Path("src/input.css").write_text(
    '@import "tailwindcss";\n\n@layer components {\n  .btn-icon {\n'
    "    margin-inline-end: calc(var(--spacing) * 2);\n  }\n}\n",
    encoding="utf-8",
)
