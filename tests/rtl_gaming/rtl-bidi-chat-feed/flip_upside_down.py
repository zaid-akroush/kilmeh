"""Gaming attempt for rtl-bidi-chat-feed: message m2 is flipped vertically with scaleY(-1);
its horizontal order is unchanged but the glyphs are upside down.

Runs in the app directory on top of the reference.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="m2"] .text{transform:scaleY(-1)}\n')
