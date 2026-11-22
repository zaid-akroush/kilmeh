"""Mutation for rtl-react-chat: the order number loses its isolation.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("src/styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="order"]{unicode-bidi:normal}' + "\n")
