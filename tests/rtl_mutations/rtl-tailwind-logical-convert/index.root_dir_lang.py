"""Mutation for rtl-tailwind-logical-convert (index.html): the dir attribute is dropped from <html> (lang stays Arabic).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = '<html dir="rtl" lang="ar-JO">'
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(text.replace(old, '<html lang="ar-JO">'), encoding="utf-8")
