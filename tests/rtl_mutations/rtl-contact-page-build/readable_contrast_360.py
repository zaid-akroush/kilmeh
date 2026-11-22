"""Mutation for rtl-contact-page-build: light grey text on white in the contact text at 360 wide.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('@media (max-width:500px){[data-testid="contact-text"]{color:#bbb}}\n')
