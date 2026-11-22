"""Mutation for rtl-contact-page-build: contact text forced to ltr.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="contact-text"]{direction:ltr}\n')
