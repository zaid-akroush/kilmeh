"""Alternative (a): text mode with newline="" and str.replace, written back with newline=""."""

import os
from pathlib import Path

app = Path(os.environ.get("KILMEH_APP", "/app"))
ts = app / "src" / "strings.ts"
with open(ts, encoding="utf-8", newline="") as f:
    text = f.read()
text = text.replace('"2.3.0"', '"2.4.0"', 1)
lines = text.split("\n")
at = next(i for i, ln in enumerate(lines) if ln.startswith("  checkout_title:"))
lines.insert(at + 1, '  checkout_subtitle: "راجع طلبك قبل الدفع",')
with open(ts, "w", encoding="utf-8", newline="") as f:
    f.write("\n".join(lines))
csv = app / "locale" / "ar.csv"
with open(csv, "a", encoding="utf-8", newline="") as f:
    f.write("checkout_subtitle,راجع طلبك قبل الدفع\r\n")
