"""Gaming attempt for rtl-react-chat: avatars are made transparent.

Runs in the app directory on top of the reference.
"""

from pathlib import Path

with Path("src/styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="avatar"]{opacity:0}' + "\n")
