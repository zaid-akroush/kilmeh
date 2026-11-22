"""Mutation for rtl-nav-fix: nav links reversed (a double flip).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write("nav{flex-direction:row-reverse}\n")
