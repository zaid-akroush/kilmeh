"""Mutation for rtl-bidi-data-cells: the version gains a visible suffix after the graded tokens.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

html = Path("index.html")
text = html.read_text(encoding="utf-8")
assert text.count("(build 77)<") == 1
html.write_text(text.replace("(build 77)<", "(build 77) x<"), encoding="utf-8")
