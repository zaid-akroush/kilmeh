"""Alternative solution: float logo, isolate controls, scale property. Runs in the app directory (the current directory)."""

from pathlib import Path

HTML = """<!doctype html>
<html lang="ar-JO" dir="RTL">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>اتصل بنا</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="top" data-testid="page-header">
    <a class="logo" href="#" data-testid="logo">شركة الأفق</a>
    <nav>
      <a href="#" data-testid="nav-link">الرئيسية</a>
      <a href="#" data-testid="nav-link">خدماتنا</a>
      <a href="#" data-testid="nav-link">اتصل بنا</a>
    </nav>
  </header>
  <main>
    <h1>تواصل معنا</h1>
    <p data-testid="contact-text">للاستفسار اتصل بنا على الرقم <span data-testid="phone-text">\u2066+962 7 9123 4567\u2069</span> أو راسلنا على <span data-testid="email-text">\u2066info@example.com\u2069</span>.</p>
    <form class="contact-form" data-testid="contact-form">
      <label>الاسم
        <input data-testid="name" dir="auto" name="name" type="text">
      </label>
      <label>البريد الإلكتروني
        <input data-testid="email-input" dir="ltr" name="email" type="email">
      </label>
      <label>رقم الهاتف
        <input data-testid="phone-input" dir="ltr" name="phone" type="text" inputmode="tel">
      </label>
    </form>
    <div class="actions">
      <button type="button" data-testid="next">
        التالي
        <svg class="icon icon-arrow" data-testid="next-icon" width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
          <line x1="2" y1="10" x2="14" y2="10" stroke="currentColor" stroke-width="2"/>
          <g data-part="head"><polyline points="12,4 18,10 12,16" fill="none" stroke="currentColor" stroke-width="2"/></g>
        </svg>
      </button>
    </div>
  </main>
</body>
</html>
"""

CSS = """* { box-sizing: border-box; }
body { margin: 0; font-family: sans-serif; line-height: 1.5; }
.top { display: flow-root; padding: 16px 24px; }
.logo { float: inline-start; font-weight: bold; margin-inline-end: 24px; }
nav { display: block; }
nav a { display: inline-block; margin-inline-end: 16px; }
main { padding: 24px; clear: both; }
.contact-form label { display: block; margin-block-end: 10px; }
.contact-form input { width: 100%; padding: 8px; }
html[dir=rtl i] .icon-arrow { scale: -1 1; }
"""

Path("index.html").write_text(HTML, encoding="utf-8")
Path("styles.css").write_text(CSS, encoding="utf-8")
