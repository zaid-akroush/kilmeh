"""Gaming attempt for rtl-bidi-chat-feed: message m1 is retyped with its Latin and number tokens
swapped, so the screen order looks right while the text no longer matches what the user typed.

Runs in the app directory on top of the reference.
"""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")
assert text.count("Ahmad") == 1
text = text.replace("Ahmad", "@@").replace("الساعة 5", "الساعة Ahmad").replace("@@", "5")
html.write_text(text, encoding="utf-8")
