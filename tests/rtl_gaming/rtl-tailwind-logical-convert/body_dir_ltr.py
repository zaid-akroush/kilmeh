"""Gaming case for rtl-tailwind-logical-convert: dir="ltr" on <body> on every page, so the whole
page reads left-to-right under <html dir="rtl"> and nothing mirrors (QA, PR 57).

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

for name in ("index.html", "notifications.html", "billing.html"):
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    assert text.count("<body ") == 1, "reference changed: update this case"
    path.write_text(text.replace("<body ", '<body dir="ltr" '), encoding="utf-8")
