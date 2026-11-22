"""Gaming attempt for rtl-react-chat: the 420px card is shrunk with a transform to fit.

Runs in the app directory on top of the reference.
"""

from pathlib import Path

with Path("src/styles.css").open("a", encoding="utf-8") as f:
    f.write(".order-card{width:420px;transform:scale(.8);transform-origin:top right}" + "\n")
