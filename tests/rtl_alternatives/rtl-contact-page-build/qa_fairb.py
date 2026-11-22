"""QA case fairB: a second fair page written differently from the reference.

Runs on the unchanged fixture; a fair page, it must score 1.
"""

from pathlib import Path

HTML = """<!doctype html>
<html lang="ar-EG" dir="rtl">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>اتصل بنا</title><link rel="stylesheet" href="styles.css"></head>
<body><header data-testid="page-header" style="display:flex;justify-content:space-between;padding-inline:1rem">
<a data-testid="logo" href="/">دار الكلمة</a>
<nav style="display:flex;gap:12px"><a data-testid="nav-link" href="/a">الأولى</a><a data-testid="nav-link" href="/b">الثانية</a><a data-testid="nav-link" href="/c">الثالثة</a></nav></header>
<section><p data-testid="contact-text">للتواصل: <bdi data-testid="phone-text">+962 7 9123 4567</bdi> — <bdi data-testid="email-text">info@example.com</bdi></p>
<form data-testid="contact-form"><table><tr><th>الاسم</th><td><input data-testid="name" style="unicode-bidi:plaintext"></td></tr>
<tr><th>البريد</th><td><input data-testid="email-input" type="email" style="direction:ltr;text-align:start"></td></tr>
<tr><th>الهاتف</th><td><input data-testid="phone-input" style="direction:ltr;text-align:start"></td></tr></table>
<button data-testid="next" type="button">التالي <svg class="icon icon-arrow" data-testid="next-icon" width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
          <line x1="2" y1="10" x2="14" y2="10" stroke="currentColor" stroke-width="2"/>
          <g data-part="head"><polyline points="12,4 18,10 12,16" fill="none" stroke="currentColor" stroke-width="2"/></g>
        </svg></button></form></section></body></html>
"""

CSS = """body{margin:0;font-family:serif;font-size:14px}
table{width:100%;max-width:340px}input{max-inline-size:100%}
.icon-arrow{scale:-1 1}
"""

Path("index.html").write_text(HTML, encoding="utf-8")
Path("styles.css").write_text(CSS, encoding="utf-8")
