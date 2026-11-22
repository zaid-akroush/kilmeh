"""Gaming attempt for rtl-contact-page-build: a too-wide form tucked into an overflow-x:auto wrapper.

Runs on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write("main{overflow-x:auto}.contact-form{min-width:600px}\n")
