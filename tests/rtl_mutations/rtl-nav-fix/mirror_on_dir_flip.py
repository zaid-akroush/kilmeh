"""Mutation for rtl-nav-fix: hero title shifts only when dir is ltr.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('html[dir="ltr"] [data-testid="hero-title"]{margin-inline-start:60px}\n')
