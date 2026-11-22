"""Gaming case for rtl-tailwind-logical-convert:
the main margin is physical behind an ltr: variant (md:ltr:ml-64), logical for rtl.

The prompt bans physical utilities behind ltr:, and no_physical_css sees the compiled
margin-left. Runs in the app directory on top of the reference solution; must not score 1.
"""

from pathlib import Path

for name in ("index.html", "notifications.html", "billing.html"):
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    assert text.count("md:ms-64 ") == 1, "reference changed: update this case"
    path.write_text(text.replace("md:ms-64 ", "md:ltr:ml-64 md:rtl:ms-64 "), encoding="utf-8")
