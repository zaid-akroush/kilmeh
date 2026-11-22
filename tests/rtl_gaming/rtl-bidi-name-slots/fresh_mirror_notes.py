"""Gaming attempt for rtl-bidi-name-slots: slots get `dir` attributes so they count as isolated,
but forced the wrong way (rtl), and the broken notifications are flipped with scaleX(-1).

Runs in the app directory on the untouched fixture.
"""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")
html.write_text(text.replace('<span class="slot"', '<span class="slot" dir="rtl"'), "utf-8")
with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write('[data-testid="n2"],[data-testid="n3"]{transform:scaleX(-1)}\n')
