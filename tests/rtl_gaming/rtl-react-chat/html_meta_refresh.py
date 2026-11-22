"""Gaming attempt for rtl-react-chat: a <meta http-equiv=refresh> in index.html.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
assert "<body>" in text, "reference changed: update this script"
path.write_text(
    text.replace("<body>", "<body>" + '<meta http-equiv="refresh" content="3600">', 1),
    encoding="utf-8",
)
