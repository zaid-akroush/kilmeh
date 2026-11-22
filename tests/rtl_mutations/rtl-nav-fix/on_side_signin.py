"""Mutation for rtl-nav-fix: sign-in first in the header, no auto margin.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="signin"]{order:-1;margin-inline-start:0}\n')
