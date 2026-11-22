"""Mutation for rtl-bidi-name-slots: the Arabic name slot stays isolated but its letters are
forced left to right with isolate-override.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="u2"]{unicode-bidi:isolate-override;direction:ltr}\n')
