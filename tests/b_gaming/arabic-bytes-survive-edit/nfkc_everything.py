"""ref: normalize all text to NFKC."""

import unicodedata
from pathlib import Path

for name in ("src/strings.ts", "locale/ar.csv", "README.md"):
    p = Path(name)
    p.write_bytes(unicodedata.normalize("NFKC", p.read_bytes().decode("utf-8")).encode("utf-8"))
