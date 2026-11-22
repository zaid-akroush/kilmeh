"""Mutation for rtl-react-chat: incoming bubbles are pushed to the end (left) side.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("src/styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="bubble-them"]{margin-inline-start:auto!important}' + "\n")
