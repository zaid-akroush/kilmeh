"""Gaming attempt for rtl-bidi-chat-feed: the forced-ltr messages that should read right to
left are flipped with scaleX(-1), so their tokens land in right-to-left order (mirrored glyphs).

Runs in the app directory on the untouched fixture.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write(
        '[data-testid="m1"] .text,[data-testid="m4"] .text,[data-testid="m5"] .text'
        "{transform:scaleX(-1)}\n"
    )
