"""ref: rewrite strings.ts from what an editor shows: no invisible characters, marks composed."""

import unicodedata
from pathlib import Path

p = Path("src/strings.ts")
text = p.read_bytes().decode("utf-8")
text = unicodedata.normalize("NFKC", text)
text = "".join(c for c in text if unicodedata.category(c) not in ("Cf", "Cc") or c == "\n")
p.write_bytes((text.rstrip() + "\n").encode("utf-8"))
