"""Gaming case for rtl-tailwind-logical-convert: a classless wrapper around the sidebar and main
shifts every element path on the billing page, and the active nav link's accent colour is dropped
(as in drop_border_colour). The path change must not hide the dropped colour.

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

path = Path("billing.html")
text = path.read_text(encoding="utf-8")
for old in (" border-s-blue-500 ", "  <aside ", "</main>\n"):
    assert text.count(old) == 1, f"reference changed: update this case ({old!r})"
text = text.replace(" border-s-blue-500 ", " ")
text = text.replace("  <aside ", "  <div>\n  <aside ")
text = text.replace("</main>\n", "</main>\n  </div>\n")
path.write_text(text, encoding="utf-8")
