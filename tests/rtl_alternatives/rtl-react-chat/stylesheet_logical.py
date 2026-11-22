"""Alternative correct solution A: no inline styles, plain CSS with logical properties, dir=auto
spans for the Latin runs, margin-inline-start: auto for own bubbles, an absolutely positioned
avatar with inset-inline-start. Runs in the app directory (the current directory)."""

import re
from pathlib import Path


def sub(path: str, pattern: str, repl: str, count: int) -> None:
    file = Path(path)
    text, n = re.subn(pattern, repl, file.read_text(encoding="utf-8"))
    assert n == count, (path, pattern, n)
    file.write_text(text, encoding="utf-8")


sub("index.html", r'<html lang="en">', '<html lang="ar" dir="rtl">', 1)

sub("src/Chat.jsx", r"\s*style=\{\{[^}]*\}\}", "", 10)  # every inline style moves to the CSS
sub(
    "src/Chat.jsx",
    r'<span data-testid="(product|order)">',
    r'<span dir="auto" data-testid="\1">',
    2,
)
sub(
    "src/Chat.jsx",
    r'<textarea data-testid="composer"',
    '<textarea dir="auto" data-testid="composer"',
    1,
)

sub("src/styles.css", r"width: 400px;", "width: 100%;", 1)
sub("src/styles.css", r"margin-left: 8px;", "margin-inline-start: 8px;", 1)
with Path("src/styles.css").open("a", encoding="utf-8") as f:
    f.write(
        "\n.row-them .avatar {\n  position: absolute;\n  inset-inline-start: 0;\n}\n"
        ".row-them .bubble {\n  margin-inline-start: 44px;\n}\n"
        ".bubble-me {\n  margin-inline-start: auto;\n}\n"
        ".time {\n  text-align: end;\n}\n"
    )
