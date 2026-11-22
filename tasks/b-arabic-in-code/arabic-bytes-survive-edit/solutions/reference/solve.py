"""Reference: edit at the byte level. bytes.replace asserts exactly one match; the CSV row is
appended in binary mode with the file's own CRLF ending."""

import os
from pathlib import Path

app = Path(os.environ.get("KILMEH_APP", "/app"))

ts = app / "src" / "strings.ts"
data = ts.read_bytes()
old = b'export const VERSION = "2.3.0";'
assert data.count(old) == 1
data = data.replace(old, b'export const VERSION = "2.4.0";')
anchor = b'  checkout_title: "'
assert data.count(anchor) == 1
end_of_line = data.index(b"\n", data.index(anchor)) + 1
entry = '  checkout_subtitle: "راجع طلبك قبل الدفع",\n'.encode()
ts.write_bytes(data[:end_of_line] + entry + data[end_of_line:])

with open(app / "locale" / "ar.csv", "ab") as f:
    f.write("checkout_subtitle,راجع طلبك قبل الدفع\r\n".encode())
