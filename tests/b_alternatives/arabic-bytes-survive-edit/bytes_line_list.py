"""Alternative (b): split the bytes into lines, edit the list, join, and append in binary mode."""

import os
from pathlib import Path

app = Path(os.environ.get("KILMEH_APP", "/app"))
ts = app / "src" / "strings.ts"
lines = ts.read_bytes().split(b"\n")
v = next(i for i, ln in enumerate(lines) if ln.startswith(b"export const VERSION"))
lines[v] = lines[v].replace(b"2.3.0", b"2.4.0")
at = next(i for i, ln in enumerate(lines) if ln.startswith(b"  checkout_title:"))
lines.insert(at + 1, '  checkout_subtitle: "راجع طلبك قبل الدفع",'.encode())
ts.write_bytes(b"\n".join(lines))
csv = app / "locale" / "ar.csv"
csv.write_bytes(csv.read_bytes() + "checkout_subtitle,راجع طلبك قبل الدفع".encode() + b"\r\n")
