"""Alternative solution: grid header, CSS isolation, CSS direction. Runs in the app directory (the current directory)."""

from pathlib import Path

HTML = """<!doctype html>
<html lang="ar" dir="rtl">
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
    <p data-testid="contact-text">للاستفسار اتصل بنا على الرقم <span data-testid="phone-text">+962 7 9123 4567</span> أو راسلنا على <span data-testid="email-text">info@example.com</span>.</p>
    <form class="contact-form" data-testid="contact-form">
      <label>الاسم
        <input data-testid="name"  name="name" type="text">
      </label>
      <label>البريد الإلكتروني
        <input data-testid="email-input"  name="email" type="email">
      </label>
      <label>رقم الهاتف
        <input data-testid="phone-input"  name="phone" type="text" inputmode="tel">
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
body { margin: 0; font: 16px/1.6 system-ui, sans-serif; }
.top { display: grid; grid-template-columns: auto 1fr; align-items: center; column-gap: 24px;
  padding-block: 16px; padding-inline: 24px; }
.logo { font-weight: 700; text-decoration: none; }
nav a { display: inline-block; padding-inline: 8px 16px; text-decoration: none; }
main { padding-inline: 24px; padding-block: 24px; }
[data-testid=phone-text], [data-testid=email-text] { unicode-bidi: isolate; }
.contact-form label { display: block; margin-block-end: 12px; }
.contact-form input { display: block; width: 100%; padding: 8px; }
[data-testid=email-input], [data-testid=phone-input] { direction: ltr; text-align: start; }
[data-testid=name] { unicode-bidi: plaintext; }
.icon-arrow:dir(rtl) { rotate: 180deg; }
"""

Path("index.html").write_text(HTML, encoding="utf-8")
Path("styles.css").write_text(CSS, encoding="utf-8")
