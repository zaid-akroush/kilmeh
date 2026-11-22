"""Mutation for rtl-react-chat: the app makes one extra same-origin request.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("src/main.jsx").open("a", encoding="utf-8") as f:
    f.write("fetch('/src/main.jsx');\n")
