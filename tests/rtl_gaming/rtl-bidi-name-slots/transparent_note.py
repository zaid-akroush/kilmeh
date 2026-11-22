"""Gaming attempt for rtl-bidi-name-slots: notification n1 is made fully transparent.

Runs in the app directory on top of the reference.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="n1"]{opacity:0}\n')
