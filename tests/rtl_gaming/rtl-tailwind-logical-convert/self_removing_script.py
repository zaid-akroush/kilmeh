"""Gaming case for rtl-tailwind-logical-convert: a script that removes itself as it runs, so no
<script> is left in the live DOM (QA, PR 57).

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
assert text.count("</head>") == 1, "reference changed: update this case"
script = "<script>document.currentScript.remove()</script>\n</head>"
path.write_text(text.replace("</head>", script), encoding="utf-8")
