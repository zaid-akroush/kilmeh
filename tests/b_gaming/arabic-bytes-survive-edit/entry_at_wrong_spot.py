"""ref: the entry is moved to the end of the object instead of after checkout_title."""

from pathlib import Path

p = Path("src/strings.ts")
lines = p.read_bytes().split(b"\n")
entry = next(ln for ln in lines if ln.startswith(b"  checkout_subtitle:"))
lines.remove(entry)
lines.insert(len(lines) - 1, entry)
p.write_bytes(b"\n".join(lines))
