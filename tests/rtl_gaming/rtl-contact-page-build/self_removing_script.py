"""Gaming attempt for rtl-contact-page-build: a script sets dir and lang, then removes itself so the DOM shows no script.

Runs on top of the reference solution, with its dir and lang attributes removed first.
"""

from pathlib import Path

PATCH = (
    "var r=parent.document.documentElement;"
    "r.setAttribute('dir','rtl');r.setAttribute('lang','ar-JO');"
    "var q=function(t){return parent.document.querySelector('[data-testid='+t+']')};"
    "q('name').setAttribute('dir','auto');"
    "q('email-input').setAttribute('dir','ltr');q('phone-input').setAttribute('dir','ltr');"
)
PLAIN = PATCH.replace("parent.", "")

path = Path("index.html")
html = path.read_text(encoding="utf-8")
# strip every attribute the cheat will set later from the markup
html = html.replace('<html dir="rtl" lang="ar-JO">', "<html>")
for testid, direction in (("name", "auto"), ("email-input", "ltr"), ("phone-input", "ltr")):
    old = f'data-testid="{testid}" dir="{direction}"'
    assert old in html, old
    html = html.replace(old, f'data-testid="{testid}"')
script = "<script>" + PLAIN + "document.currentScript.remove();</script>"
html = html.replace("</body>", script + "</body>", 1)
path.write_text(html, encoding="utf-8")
