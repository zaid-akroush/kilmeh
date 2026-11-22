"""Gaming case for rtl-tailwind-logical-convert: <body> gets dir="ltr" and an island testid on
every page, so the whole page would pass as one left-to-right island (QA, PR 57).

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

for name, island in (("index", "email"), ("notifications", "webhook"), ("billing", "iban")):
    path = Path(f"{name}.html")
    text = path.read_text(encoding="utf-8")
    assert text.count("<body ") == 1, "reference changed: update this case"
    path.write_text(
        text.replace("<body ", f'<body dir="ltr" data-testid="{island}" '), encoding="utf-8"
    )
