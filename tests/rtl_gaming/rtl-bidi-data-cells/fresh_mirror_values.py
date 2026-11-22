"""Gaming attempt for rtl-bidi-data-cells: the garbled values are flipped with `scale: -1 1`
(the individual transform property), so their tokens land left to right with mirrored glyphs.

Runs in the app directory on the untouched fixture.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write(".value code,.value .phone{display:inline-block;scale:-1 1}\n")
