"""Mutation for rtl-react-chat: the header title is 500px wide.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("src/styles.css").open("a", encoding="utf-8") as f:
    f.write(".chat-header h1{width:500px}" + "\n")
