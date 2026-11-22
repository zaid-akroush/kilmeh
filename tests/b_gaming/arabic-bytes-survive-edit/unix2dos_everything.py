"""ref: convert every LF to CRLF in all files (unix2dos)."""

from pathlib import Path

for name in ("src/strings.ts", "locale/ar.csv", "README.md"):
    p = Path(name)
    p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
