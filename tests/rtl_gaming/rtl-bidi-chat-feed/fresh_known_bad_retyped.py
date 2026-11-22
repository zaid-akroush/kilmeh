"""Gaming attempt for rtl-bidi-chat-feed (QA repro): the known-bad fix (every message forced
right to left) plus m2 and m3 retyped so that their tokens land in the graded order.

Runs in the app directory on the untouched fixture.
"""

from pathlib import Path

css = Path("styles.css")
styles = css.read_text(encoding="utf-8")
old = "  direction: ltr;\n  unicode-bidi: bidi-override;\n"
assert styles.count(old) == 1
css.write_text(styles.replace(old, "  direction: rtl;\n"), encoding="utf-8")

html = Path("index.html")
text = html.read_text(encoding="utf-8")
m2 = "Hello, الطلب جاهز؟ Thanks"
m3 = "https://shop.example/t/77 الرابط لا يعمل منذ 3 أيام"
assert text.count(m2) == 1 and text.count(m3) == 1
text = text.replace(m2, "Hello, Thanks الطلب جاهز؟")
text = text.replace(m3, "https://shop.example/t/77 3 الرابط لا يعمل منذ أيام")
html.write_text(text, encoding="utf-8")
