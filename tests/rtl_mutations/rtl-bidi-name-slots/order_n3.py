"""Mutation for rtl-bidi-name-slots: the order-number slot stays isolated but right to left.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="o1"]{direction:rtl}\n')
