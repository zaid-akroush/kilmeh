"""Mutation for rtl-react-chat: avatars sit at the end side of their bubble.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("src/styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="avatar"]{inset-inline-start:auto!important;inset-inline-end:0}' + "\n")
