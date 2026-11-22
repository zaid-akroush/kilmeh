"""Mutation for rtl-bidi-chat-feed: a visible character is added to the end of message m2
(screen order of the graded tokens is unchanged).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")
assert text.count("Thanks</p>") == 1
html.write_text(text.replace("Thanks</p>", "Thanks!</p>"), encoding="utf-8")
