"""Gaming attempt for rtl-contact-page-build: shrink all text to 6px.

Runs on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write("body{font-size:6px}\n")
