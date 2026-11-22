"""Known-bad solution (the hasty regex pass): runs in the app directory (the current directory).

Sets lang and dir on every page, then swaps only ml/mr/pl/pr/left/right with plain values and
text-left/right, on index.html and notifications.html only. It misses billing.html, borders,
corner radii, floats, scroll padding, arbitrary values and the @apply, and it turns the
left-to-right islands right-to-left too.
"""

import re
from pathlib import Path

SIDES = {"l": "s", "r": "e"}
VALUE = r"(\d+(?:\.\d+)?|px|auto)"

for name in ("index.html", "notifications.html", "billing.html"):
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    assert text.count('<html lang="en">') == 1
    text = text.replace('<html lang="en">', '<html dir="rtl" lang="ar-JO">')
    if name != "billing.html":
        text = re.sub(
            rf"(?<![\w-])(-?)([mp])([lr])-{VALUE}(?![\w\[-])",
            lambda m: f"{m[1]}{m[2]}{SIDES[m[3]]}-{m[4]}",
            text,
        )
        text = re.sub(rf"(?<![\w-])left-{VALUE}(?![\w-])", r"start-\1", text)
        text = re.sub(rf"(?<![\w-])right-{VALUE}(?![\w-])", r"end-\1", text)
        text = text.replace("text-left", "text-start").replace("text-right", "text-end")
    text = text.replace('dir="ltr"', 'dir="rtl"')
    path.write_text(text, encoding="utf-8")
