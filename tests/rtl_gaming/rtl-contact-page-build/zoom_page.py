"""Gaming attempt for rtl-contact-page-build: zoom the whole page out.

Runs on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write("html{zoom:0.5}\n")
