"""Mutation for rtl-bidi-name-slots: notification n1 is forced left to right with bidi-override
(the slot itself stays isolated).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="n1"]{direction:ltr;unicode-bidi:bidi-override}\n')
