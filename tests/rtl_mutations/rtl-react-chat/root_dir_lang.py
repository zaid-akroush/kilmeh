"""Mutation for rtl-react-chat: the page language is not Arabic.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old, new = 'lang="ar-JO"', 'lang="en"'
assert old in text, "reference changed: update this mutation"
path.write_text(text.replace(old, new, 1), encoding="utf-8")
