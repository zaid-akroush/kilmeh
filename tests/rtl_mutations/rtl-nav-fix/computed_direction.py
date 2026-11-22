"""Mutation for rtl-nav-fix: footer forced to ltr.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write("footer{direction:ltr}\n")
