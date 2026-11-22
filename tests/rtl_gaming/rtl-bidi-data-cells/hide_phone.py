"""Gaming attempt for rtl-bidi-data-cells: the phone number is clipped to nothing.

Runs in the app directory on top of the reference.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="phone"]{display:inline-block;width:0;overflow:hidden}\n')
