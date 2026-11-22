"""ref: convert every CRLF to LF in all files (dos2unix)."""

from pathlib import Path

for name in ("src/strings.ts", "locale/ar.csv", "README.md"):
    p = Path(name)
    p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n"))
