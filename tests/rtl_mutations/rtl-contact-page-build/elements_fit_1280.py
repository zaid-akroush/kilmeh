"""Mutation for rtl-contact-page-build: phone run hidden on wide screens.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('@media (min-width:800px){[data-testid="phone-text"]{display:none}}\n')
