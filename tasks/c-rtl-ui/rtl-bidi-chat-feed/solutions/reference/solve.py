"""Reference solution: each message text gets dir="auto". Runs in the app directory."""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")
assert text.count('<p class="text">') == 5
html.write_text(text.replace('<p class="text">', '<p class="text" dir="auto">'), encoding="utf-8")

css = Path("styles.css")
styles = css.read_text(encoding="utf-8")
old = "  direction: ltr;\n  unicode-bidi: bidi-override;\n"
assert styles.count(old) == 1
css.write_text(styles.replace(old, ""), encoding="utf-8")
