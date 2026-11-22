"""Mutation for rtl-contact-page-build: logo moved to the far end of the header.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="logo"]{order:9;margin-inline-start:auto}\n')
