# ruff: noqa: E402, E501, I001, UP031
from pathlib import Path

Path("index.html").write_text(
    Path("index.html")
    .read_text(encoding="utf-8")
    .replace('<html lang="en">', '<html lang="ar-JO" dir="rtl">'),
    encoding="utf-8",
)
c = Path("src/Chat.jsx").read_text(encoding="utf-8")
import re

c = re.sub(r"\s*style=\{\{[^}]*\}\}", "", c)
LRI, PDI = "⁦", "⁩"
c = c.replace(
    '<span data-testid="product">iPhone 17</span>',
    '<span data-testid="product">%siPhone 17%s</span>' % (LRI, PDI),
)
c = c.replace(
    '<span data-testid="order">ORD-48213</span>',
    '<span data-testid="order">%sORD-48213%s</span>' % (LRI, PDI),
)
c = c.replace(
    '<textarea data-testid="composer" placeholder="اكتب رسالتك" rows={1} />',
    '<input type="text" dir="auto" data-testid="composer" placeholder="اكتب رسالتك" />',
)
assert "<input" in c
Path("src/Chat.jsx").write_text(c, encoding="utf-8")
s = Path("src/styles.css").read_text(encoding="utf-8")
s = s.replace("width: 400px;", "width: min(400px, 100%);").replace(
    "margin-left: 8px;", "margin-inline-start: 8px;"
)
s = s.replace(
    ".thread {\n  display: flex;\n  flex-direction: column;",
    ".thread {\n  display: grid;\n  justify-items: start;",
)
s += """
.bubble-me { justify-self: end; }
.row-them { display: grid; grid-template-columns: auto 1fr; column-gap: 12px; align-items: start; }
.time { text-align: end; }
.composer input { flex: 1; font: inherit; }
"""
Path("src/styles.css").write_text(s, encoding="utf-8")
