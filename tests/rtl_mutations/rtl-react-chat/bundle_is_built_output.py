"""Mutation for rtl-react-chat: the app adds a second script element at run time.

Runs in the app directory on top of the reference solution. index.html stays clean, so only the
runtime check (not the static check of index.html) sees it.
"""

from pathlib import Path

with Path("src/main.jsx").open("a", encoding="utf-8") as f:
    f.write("document.body.append(document.createElement('script'));\n")
