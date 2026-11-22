"""Known-bad solution: drops the override but forces every message right to left.

Messages that start with an English word or a link still read in the wrong order. Runs in the
app directory.
"""

from pathlib import Path

css = Path("styles.css")
styles = css.read_text(encoding="utf-8")
old = "  direction: ltr;\n  unicode-bidi: bidi-override;\n"
assert styles.count(old) == 1
css.write_text(styles.replace(old, "  direction: rtl;\n"), encoding="utf-8")
