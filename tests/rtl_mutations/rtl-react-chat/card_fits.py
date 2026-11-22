"""Mutation for rtl-react-chat: the 420px card is hidden by overflow-x on its container.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("src/styles.css").open("a", encoding="utf-8") as f:
    f.write(".thread{overflow-x:hidden}\n.order-card{width:420px}" + "\n")
