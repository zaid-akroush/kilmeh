"""Mutation for rtl-order-summary-fix: logo mirrored.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="logo-icon"]{transform:scaleX(-1)}\n')
