"""Mutation for rtl-nav-fix: main cannot shrink below 600px.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write("main{min-width:600px}\n")
