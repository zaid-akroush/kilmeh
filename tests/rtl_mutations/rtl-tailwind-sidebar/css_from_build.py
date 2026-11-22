"""Mutation for rtl-tailwind-sidebar: an inline <style> element is added (harmless rule).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = '<link rel="stylesheet" href="/dist/app.css">'
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(
    text.replace(old, '<link rel="stylesheet" href="/dist/app.css">\n  <style>/* note */</style>'),
    encoding="utf-8",
)
