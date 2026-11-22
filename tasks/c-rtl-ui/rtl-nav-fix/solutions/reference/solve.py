"""Reference solution: runs in the app directory (the current directory)."""

from pathlib import Path


def edit(name, pairs):
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        assert text.count(old) == 1, f"{name}: expected one {old!r}"
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


edit("index.html", [('<html lang="en">', '<html dir="rtl" lang="ar-JO">')])
edit(
    "styles.css",
    [
        ("  float: left;\n", ""),
        ("  margin-left: 16px;\n", "  margin-inline-start: 16px;\n"),
        ("  margin-left: auto;\n", "  margin-inline-start: auto;\n"),
        ("  text-align: left;\n", "  text-align: start;\n"),
        ("  padding-left: 48px;\n", "  padding-inline-start: 48px;\n"),
    ],
)
