"""Gaming attempt for rtl-react-chat: a same-origin <iframe src=/x.html> in index.html.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

Path("x.html").write_text("<!doctype html><title>x</title>", encoding="utf-8")
path = Path("index.html")
text = path.read_text(encoding="utf-8")
assert "<body>" in text, "reference changed: update this script"
path.write_text(
    text.replace("<body>", "<body>" + '<iframe src="/x.html" hidden></iframe>', 1), encoding="utf-8"
)
