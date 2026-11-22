"""Mutation for rtl-bidi-data-cells: the function-name cell is laid out as a reversed flex row,
so the opening Arabic words move to the left of the value (directions are unchanged).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="r-code"] td.value{display:flex;flex-direction:row-reverse}\n')
