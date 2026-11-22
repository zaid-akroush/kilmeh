"""Mutation for rtl-order-summary-fix: the 420px table is hidden by overflow-x on its container.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write("main{overflow-x:hidden}\ntable.summary{width:420px}\n")
