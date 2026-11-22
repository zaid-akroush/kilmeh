"""Mutation for rtl-react-chat: the composer is forced right to left.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("src/Chat.jsx")
text = path.read_text(encoding="utf-8")
old, new = '<textarea dir="auto"', '<textarea dir="rtl"'
assert old in text, "reference changed: update this mutation"
path.write_text(text.replace(old, new, 1), encoding="utf-8")
