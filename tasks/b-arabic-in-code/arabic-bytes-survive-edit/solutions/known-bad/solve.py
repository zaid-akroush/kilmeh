"""Known-bad: a correct edit done in text mode. Universal newlines turn the CSV's CRLF into LF
when it is read, and the file is written back (and the row appended) with LF."""

import os
from pathlib import Path

app = Path(os.environ.get("KILMEH_APP", "/app"))

ts = app / "src" / "strings.ts"
text = ts.read_text(encoding="utf-8")
text = text.replace('"2.3.0"', '"2.4.0"')
lines = text.split("\n")
at = next(i for i, ln in enumerate(lines) if ln.startswith("  checkout_title:"))
lines.insert(at + 1, '  checkout_subtitle: "راجع طلبك قبل الدفع",')
ts.write_text("\n".join(lines), encoding="utf-8")

csv = app / "locale" / "ar.csv"
body = csv.read_text(encoding="utf-8")
csv.write_text(body + "checkout_subtitle,راجع طلبك قبل الدفع\n", encoding="utf-8")
