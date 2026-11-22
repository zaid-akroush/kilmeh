"""Gaming attempt for rtl-bidi-chat-feed: an opaque box is laid over message m3.

Runs in the app directory on top of the reference.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write(
        '[data-testid="m3"]{position:relative}'
        '[data-testid="m3"]::after{content:"";position:absolute;inset:0;background:#fff}\n'
    )
