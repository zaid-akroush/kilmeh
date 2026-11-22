"""Alternative for rtl-bidi-data-cells (QA): the reference fix, with each table cell on its own
indented line (whitespace between cells that never renders).

Runs in the app directory on the untouched fixture.
"""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")
for testid in ("path", "version", "phone", "fn"):
    attr = f'data-testid="{testid}"'
    assert text.count(attr) == 1, testid
    text = text.replace(attr, f'{attr} dir="ltr"')
text = text.replace("<td", "\n          <td").replace("</tr>", "\n        </tr>")
html.write_text(text, encoding="utf-8")
