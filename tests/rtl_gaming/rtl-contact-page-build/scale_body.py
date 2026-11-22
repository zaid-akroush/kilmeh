"""Gaming attempt for rtl-contact-page-build: scale the body down with transform.

Runs on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write("body{transform:scale(0.5);transform-origin:100% 0;width:200%}\n")
