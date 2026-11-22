"""ref: formatter style: trim trailing spaces and end each file with a final newline."""

from pathlib import Path

for name in ("src/strings.ts", "locale/ar.csv", "README.md"):
    p = Path(name)
    lines = [ln.rstrip(b" ") for ln in p.read_bytes().split(b"\n")]
    p.write_bytes(b"\n".join(lines).rstrip(b"\n") + b"\n")
