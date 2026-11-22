"""Gaming case for rtl-tailwind-logical-convert, run on a fresh fixture: lang and dir are set and
the whole body is flipped with transform: scaleX(-1) (-scale-x-100); no class is converted.

Must not score 1.
"""

from pathlib import Path

for name in ("index.html", "notifications.html", "billing.html"):
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    assert text.count('<html lang="en">') == 1 and text.count('<body class="') == 1
    text = text.replace('<html lang="en">', '<html dir="rtl" lang="ar-JO">')
    text = text.replace('<body class="', '<body class="-scale-x-100 ')
    path.write_text(text, encoding="utf-8")
