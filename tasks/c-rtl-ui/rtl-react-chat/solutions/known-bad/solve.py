"""Known-bad solution (a naive agent): only sets dir and lang on <html>. Runs in the app directory."""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")
assert text.count('<html lang="en">') == 1
html.write_text(text.replace('<html lang="en">', '<html lang="ar" dir="rtl">'), encoding="utf-8")
