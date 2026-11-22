"""Known-bad solution: flips every SVG, forces ltr on all inputs, isolates nothing.

The logo and the play icon get mirrored too, the name field no longer follows its text, and
the table stays 420px wide. Runs in the app directory.
"""

import re
from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")
text, n = re.subn(r"<input ", '<input dir="ltr" ', text)
assert n == 3
html.write_text(text, encoding="utf-8")

with Path("styles.css").open("a", encoding="utf-8") as css:
    css.write("\nsvg {\n  transform: scaleX(-1);\n}\n")
