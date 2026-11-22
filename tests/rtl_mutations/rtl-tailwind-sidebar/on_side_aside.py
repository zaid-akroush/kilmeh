"""Mutation for rtl-tailwind-sidebar: at 1280px the sidebar sits left of the page centre, and
the main content is moved to its left, so only on_side_aside fails (logical classes only).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
for old, new in (("start-0 ", "start-0 md:start-[704px] "), ("ms-64 ", "ms-64 md:ms-[960px] ")):
    assert text.count(old) == 1, "reference changed: update this mutation"
    text = text.replace(old, new)
path.write_text(text, encoding="utf-8")
