"""Known-bad solution (a naive agent): adds dir="rtl" and patches the nav with row-reverse.

The physical rules stay, and the page language stays "en". Runs in the app directory.
"""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")
assert text.count('<html lang="en">') == 1
html.write_text(text.replace('<html lang="en">', '<html dir="rtl" lang="en">'), encoding="utf-8")

with Path("styles.css").open("a", encoding="utf-8") as css:
    css.write("\nnav {\n  flex-direction: row-reverse;\n}\n")
