"""Mutation for rtl-order-summary-fix: phone run loses its isolation.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="phone"]{unicode-bidi:normal}\n')
