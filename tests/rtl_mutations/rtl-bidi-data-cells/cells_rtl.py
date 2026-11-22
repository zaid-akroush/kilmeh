"""Mutation for rtl-bidi-data-cells: the header cells are forced left to right.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write("th{direction:ltr}\n")
