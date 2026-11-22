"""Mutation for rtl-nav-fix: an unused rule with a physical side.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write(".unused{padding-left:3px}\n")
