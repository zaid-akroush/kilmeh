"""Reference solution: each technical value gets dir="ltr" (isolated, left to right).

Runs in the app directory.
"""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")
for testid in ("path", "version", "phone", "fn"):
    attr = f'data-testid="{testid}"'
    assert text.count(attr) == 1, testid
    text = text.replace(attr, f'{attr} dir="ltr"')
html.write_text(text, encoding="utf-8")
