"""Gaming case for rtl-tailwind-logical-convert: <html> keeps lang="en" and no dir in the file; a
self-removing script sets dir="rtl" and lang="ar-JO" at load time (QA, PR 57).

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

path = Path("billing.html")
text = path.read_text(encoding="utf-8")
for old in ('<html dir="rtl" lang="ar-JO">', "</head>"):
    assert text.count(old) == 1, f"reference changed: update this case ({old!r})"
text = text.replace('<html dir="rtl" lang="ar-JO">', '<html lang="en">')
script = (
    "<script>document.documentElement.dir = 'rtl'; document.documentElement.lang = 'ar-JO';"
    " document.currentScript.remove()</script>\n</head>"
)
path.write_text(text.replace("</head>", script), encoding="utf-8")
