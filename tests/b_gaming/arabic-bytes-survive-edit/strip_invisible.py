"""ref: strip every format character (category Cf) from all files."""

import unicodedata
from pathlib import Path

for name in ("src/strings.ts", "locale/ar.csv", "README.md"):
    p = Path(name)
    text = p.read_bytes().decode("utf-8")
    p.write_bytes("".join(c for c in text if unicodedata.category(c) != "Cf").encode("utf-8"))
