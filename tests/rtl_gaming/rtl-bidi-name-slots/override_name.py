"""Gaming attempt for rtl-bidi-name-slots (review probe): the name slot is isolated but its
letters are forced right to left with isolate-override, so "Ahmad" shows reversed.

Runs in the app directory on top of the reference.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="u1"]{direction:rtl;unicode-bidi:isolate-override}\n')
