"""Reference solution: runs in the app directory (the current directory)."""

import re
from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")

# isolate the four Latin and number runs
for run in ("inv", "phone", "user", "price"):
    text, n = re.subn(
        rf'<span data-testid="{run}">(.*?)</span>', rf'<bdi data-testid="{run}">\1</bdi>', text
    )
    assert n == 1, run

# email and phone read left to right; the name follows what the user types
for testid, direction in (("email", "ltr"), ("phone-input", "ltr"), ("name", "auto")):
    text, n = re.subn(
        rf'(<input data-testid="{testid}")', rf'\1 dir="{direction}"', text, count=1
    )
    assert n == 1, testid
html.write_text(text, encoding="utf-8")

css = Path("styles.css")
styles = css.read_text(encoding="utf-8")
assert styles.count("width: 420px;") == 1
styles = styles.replace("width: 420px;", "width: 100%;")
styles += "\n[dir=rtl] .icon-arrow {\n  transform: scaleX(-1);\n}\n"
css.write_text(styles, encoding="utf-8")
