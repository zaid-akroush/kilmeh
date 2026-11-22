"""Mutation for rtl-contact-page-build: a 900px decorative bar after the content.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
assert "</body>" in text
bar = '<div style="width:900px;height:4px"></div>\n</body>'
path.write_text(text.replace("</body>", bar, 1), encoding="utf-8")
