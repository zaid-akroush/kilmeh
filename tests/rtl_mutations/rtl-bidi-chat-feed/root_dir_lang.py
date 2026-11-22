"""Mutation for rtl-bidi-chat-feed: the page language is no longer Arabic.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

html = Path("index.html")
html.write_text(
    html.read_text(encoding="utf-8").replace('lang="ar"', 'lang="en"', 1), encoding="utf-8"
)
