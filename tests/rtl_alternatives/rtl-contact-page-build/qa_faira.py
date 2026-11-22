"""QA case fairA: a fair page written differently from the reference.

Runs on the unchanged fixture; a fair page, it must score 1.
"""

from pathlib import Path

HTML = """<!doctype html>
<html dir="rtl" lang="ar">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>اتصل بنا</title><link rel="stylesheet" href="styles.css"></head>
<body><header data-testid="page-header"><div class="bar"><a data-testid="logo" href="#">مكتب النور</a>
<nav aria-label="main"><a data-testid="nav-link" href="#">البداية</a><a data-testid="nav-link" href="#">من نحن</a><a data-testid="nav-link" href="#">تواصل</a></nav></div></header>
<main><h1>راسلنا</h1>
<p data-testid="contact-text">يمكنك الاتصال على <span data-testid="phone-text" dir="ltr">+962 7 9123 4567</span> أو مراسلتنا عبر <span data-testid="email-text" dir="ltr">info@example.com</span> في أي وقت.</p>
<form data-testid="contact-form"><dl><dt>الاسم</dt><dd><input data-testid="name" dir="auto" aria-label="الاسم"></dd>
<dt>البريد</dt><dd><input data-testid="email-input" type="email" dir="ltr" aria-label="البريد"></dd>
<dt>الهاتف</dt><dd><input data-testid="phone-input" dir="ltr" aria-label="الهاتف"></dd></dl>
<button data-testid="next" type="button"><span>متابعة</span><svg class="icon icon-arrow" data-testid="next-icon" width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
          <line x1="2" y1="10" x2="14" y2="10" stroke="currentColor" stroke-width="2"/>
          <g data-part="head"><polyline points="12,4 18,10 12,16" fill="none" stroke="currentColor" stroke-width="2"/></g>
        </svg></button></form></main></body></html>
"""

CSS = """body{margin:0;font:16px/1.5 sans-serif}
.bar{display:grid;grid-template-columns:auto 1fr;gap:1rem;padding:1rem;align-items:center}
nav{display:flex;gap:1rem;flex-wrap:wrap}
main{padding:1rem}
dl{display:grid;grid-template-columns:6rem 1fr;gap:.5rem}
dd{margin:0}dd input{width:100%;box-sizing:border-box}
.icon-arrow:dir(rtl){rotate:180deg}
button{display:inline-flex;gap:.5rem;align-items:center;padding-inline:1rem}
"""

Path("index.html").write_text(HTML, encoding="utf-8")
Path("styles.css").write_text(CSS, encoding="utf-8")
