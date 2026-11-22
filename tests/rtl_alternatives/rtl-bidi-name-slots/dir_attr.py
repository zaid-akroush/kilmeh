"""Alternative for rtl-bidi-name-slots: `dir="auto"` on every slot span.

Runs in the app directory on the untouched fixture.
"""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")
assert text.count('<span class="slot"') == 4
html.write_text(text.replace('<span class="slot"', '<span class="slot" dir="auto"'), "utf-8")
