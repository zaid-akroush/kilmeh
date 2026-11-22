"""Mutation for rtl-contact-page-build: a 10px fixed, pointer-events:none white box over the header at 360 wide.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write(
        "@media (max-width:500px){body::after{content:'';position:fixed;top:0;inset-inline-start:0;width:10px;height:10px;background:#fff;pointer-events:none}}\n"
    )
