"""Alternative for rtl-bidi-chat-feed: CSS `unicode-bidi: plaintext` on every message text.

Runs in the app directory on the untouched fixture.
"""

from pathlib import Path

css = Path("styles.css")
styles = css.read_text(encoding="utf-8")
old = "  direction: ltr;\n  unicode-bidi: bidi-override;\n"
assert styles.count(old) == 1
css.write_text(styles.replace(old, "  unicode-bidi: plaintext;\n"), encoding="utf-8")
