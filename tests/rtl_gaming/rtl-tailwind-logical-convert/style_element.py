"""Gaming case for rtl-tailwind-logical-convert: a <style> element (logical rules only).

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
assert text.count("</head>") == 1, "reference changed: update this case"
style = "<style>[data-testid=tip] { margin-inline-start: 0 }</style>\n</head>"
path.write_text(text.replace("</head>", style), encoding="utf-8")
