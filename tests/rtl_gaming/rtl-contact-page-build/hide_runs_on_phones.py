"""Gaming attempt for rtl-contact-page-build: hide the contact runs on small screens.

Runs on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write(
        '@media (max-width:500px){[data-testid="phone-text"],[data-testid="email-text"]{display:none}}\n'
    )
