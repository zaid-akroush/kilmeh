"""Mutation for rtl-bidi-name-slots: the Arabic name slot loses its isolation (no geometry check
covers it, so only bidi_isolated sees it).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="u2"]{unicode-bidi:normal}\n')
