"""Gaming attempt for rtl-react-chat: a <link rel=modulepreload> in index.html.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
assert "<body>" in text, "reference changed: update this script"
path.write_text(
    text.replace("<body>", "<body>" + '<link rel="modulepreload" href="/src/main.jsx">', 1),
    encoding="utf-8",
)
