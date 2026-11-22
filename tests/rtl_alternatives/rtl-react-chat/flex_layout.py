"""Alternative correct solution B: flexbox instead of margins and absolute positioning
(align-self: flex-end for own bubbles, a flex row with the avatar as its first item), dir and lang
set from main.jsx instead of index.html, span dir=ltr for the Latin runs, a plaintext composer
(unicode-bidi) instead of dir=auto, gap instead of a margin on the send button.
Runs in the app directory (the current directory)."""

import re
from pathlib import Path


def sub(path: str, pattern: str, repl: str, count: int) -> None:
    file = Path(path)
    text, n = re.subn(pattern, repl, file.read_text(encoding="utf-8"))
    assert n == count, (path, pattern, n)
    file.write_text(text, encoding="utf-8")


main = Path("src/main.jsx")
main.write_text(
    "document.documentElement.lang = 'ar-JO';\n"
    "document.documentElement.dir = 'rtl';\n" + main.read_text(encoding="utf-8"),
    encoding="utf-8",
)

sub("src/Chat.jsx", r"\s*style=\{\{[^}]*\}\}", "", 10)
sub(
    "src/Chat.jsx", r'<span data-testid="(product|order)">', r'<span dir="ltr" data-testid="\1">', 2
)
sub(
    "src/Chat.jsx",
    r'<textarea data-testid="composer"',
    '<textarea style={{ unicodeBidi: "plaintext" }} data-testid="composer"',
    1,
)

sub("src/styles.css", r"\.send \{\n  margin-left: 8px;\n\}", ".composer {\n  gap: 8px;\n}", 1)
with Path("src/styles.css").open("a", encoding="utf-8") as f:
    f.write(
        "\n.row-them {\n  display: flex;\n  align-items: flex-start;\n  gap: 12px;\n}\n"
        ".avatar {\n  flex: none;\n}\n"
        ".thread > .bubble-me {\n  align-self: flex-end;\n}\n"
        ".time {\n  text-align: end;\n}\n"
        ".order-card {\n  width: 400px;\n  max-width: 100%;\n}\n"
    )
