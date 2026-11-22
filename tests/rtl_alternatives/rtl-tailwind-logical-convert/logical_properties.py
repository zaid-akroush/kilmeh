"""Alternative correct solution for rtl-tailwind-logical-convert: no logical Tailwind utilities.

The sidebar shell (sidebar, nav links, main) moves into hand-written, unlayered CSS in
`src/input.css` with logical properties, and every other physical utility becomes a Tailwind
arbitrary property with a logical property (`[margin-inline-start:3px]`, `[float:inline-start]`,
`[border-start-start-radius:...]`). No `ms-*`, `start-*`, `rounded-s-*` or `text-start`.
Runs in the app directory on a fresh copy of the fixture; must score 1.
"""

import re
from pathlib import Path

CSS = """@import "tailwindcss";

.btn-icon {
  margin-inline-end: calc(var(--spacing) * 2);
}
@media (width >= 48rem) {
  .shell-sidebar {
    inset-inline-start: 0;
    border-inline-end-style: solid;
    border-inline-end-width: 1px;
  }
  .shell-main {
    margin-inline-start: 16rem;
    padding-inline-start: 2rem;
  }
}
.nav-item {
  border-inline-start: 4px solid transparent;
  padding-inline-start: 0.75rem;
  border-start-end-radius: var(--radius-md);
  border-end-end-radius: var(--radius-md);
}
.nav-item.is-active {
  border-inline-start-color: var(--color-blue-500);
}
.nav-item:not(.is-active):hover {
  border-inline-start-color: var(--color-slate-300);
}
"""

NAV = {"rounded-r-md", "border-l-4", "border-l-transparent", "pl-3", "hover:border-l-slate-300"}

TOKENS = {
    "md:left-0": "shell-sidebar",
    "md:border-r": "",
    "md:ml-64": "shell-main",
    "md:pl-8": "",
    "float-left": "[float:inline-start]",
    "float-right": "[float:inline-end]",
    "mr-4": "[margin-inline-end:1rem]",
    "ml-2": "[margin-inline-start:0.5rem]",
    "ml-[3px]": "[margin-inline-start:3px]",
    "-ml-px": "[margin-inline-start:-1px]",
    "ml-auto": "[margin-inline-start:auto]",
    "text-left": "[text-align:start]",
    "text-right": "[text-align:end]",
    "rounded-l-md": "[border-start-start-radius:var(--radius-md)] [border-end-start-radius:var(--radius-md)]",
    "rounded-r-md": "[border-start-end-radius:var(--radius-md)] [border-end-end-radius:var(--radius-md)]",
    "rounded-r": "[border-start-end-radius:0.25rem] [border-end-end-radius:0.25rem]",
    "rounded-tl-lg": "[border-start-start-radius:var(--radius-lg)]",
    "rounded-br-md": "[border-end-end-radius:var(--radius-md)]",
    "border-l-4": "[border-inline-start-style:solid] [border-inline-start-width:4px]",
    "border-l-amber-400": "[border-inline-start-color:var(--color-amber-400)]",
    "border-l-blue-500": "[border-inline-start-color:var(--color-blue-500)]",
    "border-l-slate-300": "[border-inline-start-color:var(--color-slate-300)]",
    "hover:border-r-2": "hover:[border-inline-end-width:2px]",
    "scroll-pl-4": "[scroll-padding-inline-start:1rem]",
    "pl-4": "[padding-inline-start:1rem]",
    "pl-5": "[padding-inline-start:1.25rem]",
    "pl-6": "[padding-inline-start:1.5rem]",
    "pr-4": "[padding-inline-end:1rem]",
    "pr-8": "[padding-inline-end:2rem]",
    "left-0": "[inset-inline-start:0]",
    "right-3": "[inset-inline-end:0.75rem]",
}


def fix(match):
    tokens = match.group(1).split()
    if NAV <= set(tokens) or {"border-l-blue-500", "pl-3"} <= set(tokens):  # a nav link
        active = "border-l-blue-500" in tokens
        tokens = [t for t in tokens if t not in NAV | {"border-l-blue-500"}]
        tokens.append("nav-item is-active" if active else "nav-item")
    out = " ".join(TOKENS.get(t, t) for t in tokens).split()
    return 'class="' + " ".join(out) + '"'


Path("src/input.css").write_text(CSS, encoding="utf-8")
for name in ("index.html", "notifications.html", "billing.html"):
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    assert text.count('<html lang="en">') == 1
    text = text.replace('<html lang="en">', '<html dir="rtl" lang="ar-JO">')
    path.write_text(re.sub(r'class="([^"]*)"', fix, text), encoding="utf-8")
