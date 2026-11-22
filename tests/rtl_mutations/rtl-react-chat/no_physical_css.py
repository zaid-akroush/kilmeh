"""Mutation for rtl-react-chat: a physical margin-left that changes nothing.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("src/styles.css").open("a", encoding="utf-8") as f:
    f.write(".time{margin-left:3px}" + "\n")
