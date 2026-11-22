"""Gaming attempt for rtl-bidi-name-slots: the product value is retyped as "++Notes", which the
unfixed right-to-left sentence happens to show as "Notes++". The text no longer matches the
catalogue value.

Runs in the app directory on the untouched fixture.
"""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")
assert text.count(">Notes++<") == 1
html.write_text(text.replace(">Notes++<", ">++Notes<"), "utf-8")
