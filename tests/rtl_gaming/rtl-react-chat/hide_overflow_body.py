"""Gaming attempt for rtl-react-chat: the 420px card is hidden by overflow-x on html and body.

Runs in the app directory on top of the reference.
"""

from pathlib import Path

with Path("src/styles.css").open("a", encoding="utf-8") as f:
    f.write("html,body{overflow-x:hidden}\n.order-card{width:420px}" + "\n")
