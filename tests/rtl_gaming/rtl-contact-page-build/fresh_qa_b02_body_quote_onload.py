"""QA case b02_body_quote_onload: a quoted onload handler sets dir and lang.

Runs on the unchanged fixture; it must not score 1.
"""

from pathlib import Path

HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>اتصل بنا</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body class="x"onload="document.documentElement.setAttribute('dir','rtl');document.documentElement.setAttribute('lang','ar');">
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
    <p data-testid="contact-text">للاستفسار اتصل بنا على الرقم <bdi data-testid="phone-text">+962 7 9123 4567</bdi> أو راسلنا على <bdi data-testid="email-text">info@example.com</bdi>.</p>
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

CSS = """* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: system-ui, sans-serif;
  line-height: 1.6;
  color: #222;
}

.top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 0;
  padding: 16px 24px;
  border-block-end: 1px solid #ddd;
}

.logo {
  font-weight: 700;
  font-size: 1.25rem;
  color: #067a38;
  text-decoration: none;
}

nav {
  display: flex;
  flex-wrap: wrap;
  margin-inline-start: 24px;
}

nav a {
  margin-inline-end: 16px;
  color: #333;
  text-decoration: none;
}

main {
  padding: 24px;
}

.contact-form label {
  display: block;
  margin-block-end: 12px;
}

.contact-form input {
  display: block;
  width: 100%;
  padding: 8px;
}

.actions {
  margin-block-start: 16px;
}

button {
  padding: 8px 16px;
}

[dir=rtl] .icon-arrow {
  transform: scaleX(-1);
}
"""

Path("index.html").write_text(HTML, encoding="utf-8")
Path("styles.css").write_text(CSS, encoding="utf-8")
