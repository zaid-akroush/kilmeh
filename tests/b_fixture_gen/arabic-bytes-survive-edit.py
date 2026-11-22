"""Builds the fixture of arabic-bytes-survive-edit: `python3 gen.py OUT_DIR`.

Escape-only: every invisible, combining or direction-control character is written as a named
escape below, so each one in the fixture is intended. The visible Arabic is drafted by an agent
and listed in the task's REVIEW.md. A repo test (tests/test_b_bytes.py) runs this script and
compares the bytes with the committed fixture and with tests/golden/.
"""

import sys
from pathlib import Path

RLM, LRM = "\u200f", "\u200e"
LRE, RLE, PDF = "\u202a", "\u202b", "\u202c"
LRI, RLI, FSI, PDI = "\u2066", "\u2067", "\u2068", "\u2069"
ALM = "\u061c"
ZWNJ, ZWJ = "\u200c", "\u200d"
SHADDA, FATHA = "\u0651", "\u064e"  # canonical order is FATHA (ccc 30) then SHADDA (ccc 33)
MADDAH = "\u0653"  # alef + MADDAH composes to U+0622 under NFC
ALLAH = "\ufdf2"  # NFKC expands it to its letters
NBSP = "\u00a0"
FAMILY = "\U0001f468" + ZWJ + "\U0001f469" + ZWJ + "\U0001f467"

TS_LINES = [
    "// Storefront UI strings. This module is never executed; it is only edited.",
    'export const VERSION = "2.3.0";',
    "",
    "export const strings = {",
    '  welcome: "مرحبا بكم في متجرنا",',
    f'  phone: "الهاتف: {RLM}+962 6 555 0100{LRM}",',
    f'  embed: "{RLE}نص عربي{PDF} and {LRE}English text{PDF}",',
    f'  isolates: "{LRI}abc{PDI} {RLI}نص{PDI} {FSI}مرحبا hello{PDI}",',
    f'  alm: "رقم {ALM}+٩٦٢",',
    f'  zwnj: "كتاب{ZWNJ}ها",',
    f'  zwj_word: "ه{ZWJ}ه{ZWJ}ه",',
    f'  family: "{FAMILY}",',
    f'  marks: "ب{SHADDA}{FATHA}ب",',
    f'  nfd: "ا{MADDAH}خر",',
    f'  allah: "{ALLAH}",',
    f'  nbsp: "10{NBSP}JD",',
    '  checkout_title: "إتمام الشراء",',
    '  cart_empty: "سلتك فارغة",',
    '  trailing: "قيمة",   ',
    "};",
]
CSV_ROWS = [
    "key,value",
    "welcome,مرحبا بكم في متجرنا",
    "checkout_title,إتمام الشراء",
    "cart_empty,سلتك فارغة",
]
README = (
    "# Storefront strings\n\n"
    "`src/strings.ts` holds the UI strings and `locale/ar.csv` the Arabic export.\n"
    "Neither file is built or run in this repository.\n"
)

FILES = {
    "src/strings.ts": "\n".join(TS_LINES).encode("utf-8"),  # LF, no final newline
    "locale/ar.csv": "".join(r + "\r\n" for r in CSV_ROWS).encode("utf-8"),  # CRLF
    "README.md": README.encode("utf-8"),
}

if __name__ == "__main__":
    out = Path(sys.argv[1])
    for name, data in FILES.items():
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        (out / name).write_bytes(data)
