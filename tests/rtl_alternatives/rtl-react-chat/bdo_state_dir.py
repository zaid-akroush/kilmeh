# ruff: noqa: E402, E501, I001
from pathlib import Path
import re

Path("index.html").write_text(
    Path("index.html")
    .read_text(encoding="utf-8")
    .replace('<html lang="en">', '<html lang="ar-JO" dir="rtl">'),
    encoding="utf-8",
)
c = Path("src/Chat.jsx").read_text(encoding="utf-8")
c = re.sub(r"\s*style=\{\{[^}]*\}\}", "", c)
c = c.replace(
    '<span data-testid="product">iPhone 17</span>',
    '<bdo dir="ltr" data-testid="product">iPhone 17</bdo>',
)
c = c.replace(
    '<span data-testid="order">ORD-48213</span>',
    '<bdo dir="ltr" data-testid="order">ORD-48213</bdo>',
)
c = c.replace(
    "export default function Chat() {\n",
    "import { useState } from 'react';\nexport default function Chat() {\n  const [text, setText] = useState('');\n  const dir = /^[\\s\\d\\p{P}]*\\p{Script=Arabic}/u.test(text) ? 'rtl' : 'ltr';\n",
)
c = c.replace(
    '<textarea data-testid="composer"',
    '<textarea dir={dir} value={text} onChange={(e) => setText(e.target.value)} data-testid="composer"',
)
Path("src/Chat.jsx").write_text(c, encoding="utf-8")
s = Path("src/styles.css").read_text(encoding="utf-8")
s = s.replace("width: 400px;", "width: 100%;").replace(
    "margin-left: 8px;", "margin-inline-start: 8px;"
)
s += """
.bubble-me { margin-inline-start: auto; border-end-start-radius: 2px; }
.row-them { display: flex; gap: 12px; align-items: flex-start; }
.row-them .bubble { border-end-start-radius: 2px; }
.time { text-align: end; }
"""
Path("src/styles.css").write_text(s, encoding="utf-8")
