"""Mutation for rtl-contact-page-build: phone run loses its isolation.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="phone-text"]{unicode-bidi:normal}\n')
