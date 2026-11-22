"""Mutation for rtl-bidi-name-slots: a visible character is added after the order number in n3
(the graded tokens are unchanged).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")
assert text.count("#A-1024<") == 1
html.write_text(text.replace("#A-1024<", "#A-1024.<"), encoding="utf-8")
