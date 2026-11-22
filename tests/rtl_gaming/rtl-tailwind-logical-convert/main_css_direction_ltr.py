"""Gaming case for rtl-tailwind-logical-convert: <main> is forced left-to-right with
`direction: ltr; unicode-bidi: isolate` in src/input.css on every page (QA, PR 57).

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

with Path("src/input.css").open("a", encoding="utf-8") as f:
    f.write("main{direction:ltr;unicode-bidi:isolate}\n")
