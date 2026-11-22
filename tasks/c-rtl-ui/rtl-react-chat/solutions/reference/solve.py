"""Reference solution: runs in the app directory (the current directory)."""

from pathlib import Path


def edit(path: str, pairs: list[tuple[str, str, int]]) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    for old, new, count in pairs:
        assert text.count(old) == count, (path, old, text.count(old))
        text = text.replace(old, new)
    file.write_text(text, encoding="utf-8")


# the page is Arabic and right-to-left
edit("index.html", [('<html lang="en">', '<html lang="ar-JO" dir="rtl">', 1)])

edit(
    "src/Chat.jsx",
    [
        # logical inline styles
        ("left: 0 }}", "insetInlineStart: 0 }}", 2),
        ("marginLeft: 44", "marginInlineStart: 44", 2),
        ("marginLeft: 'auto'", "marginInlineStart: 'auto'", 2),
        ("textAlign: 'right'", "textAlign: 'end'", 4),
        # isolate the Latin runs
        ('<span data-testid="product">iPhone 17</span>', '<bdi data-testid="product">iPhone 17</bdi>', 1),
        ('<span data-testid="order">ORD-48213</span>', '<bdi data-testid="order">ORD-48213</bdi>', 1),
        # the composer follows what is typed
        ('<textarea data-testid="composer"', '<textarea dir="auto" data-testid="composer"', 1),
    ],
)

edit(
    "src/styles.css",
    [
        ("width: 400px;", "width: 100%;", 1),
        ("margin-left: 8px;", "margin-inline-start: 8px;", 1),
    ],
)
