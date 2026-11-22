"""Mutation for rtl-order-summary-fix: next arrow not flipped in rtl.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[dir="rtl"] [data-testid="next-icon"]{transform:none}\n')
