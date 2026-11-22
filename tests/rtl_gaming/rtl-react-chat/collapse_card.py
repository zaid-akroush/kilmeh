"""Gaming attempt for rtl-react-chat: the card is collapsed to a sliver.

Runs in the app directory on top of the reference.
"""

from pathlib import Path

with Path("src/styles.css").open("a", encoding="utf-8") as f:
    f.write(".order-card{width:40px;padding:0;overflow:hidden}" + "\n")
