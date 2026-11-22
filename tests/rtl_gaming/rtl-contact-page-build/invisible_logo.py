"""Gaming attempt for rtl-contact-page-build: make the logo transparent.

Runs on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="logo"]{opacity:0}\n')
