"""Mutation for rtl-react-chat: index.html gets an inline event-handler attribute.

Runs in the app directory on top of the reference solution. The handler never runs, so the page
and the runtime script check are unchanged: only the static check of index.html sees it.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
assert "<body>" in text, "reference changed: update this mutation"
path.write_text(text.replace("<body>", '<body onclick="void 0">', 1), encoding="utf-8")
