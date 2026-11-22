"""Gaming case for rtl-tailwind-logical-convert:
the main margin comes from a class that exists only in a hand-edited dist/app.css.

Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

for name in ("index.html", "notifications.html", "billing.html"):
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    assert text.count("md:ms-64 ") == 1, "reference changed: update this case"
    path.write_text(text.replace("md:ms-64 ", "my-main "), encoding="utf-8")
with Path("dist/app.css").open("a", encoding="utf-8") as f:
    f.write("@media (width >= 48rem) { .my-main { margin-inline-start: 16rem } }\n")
