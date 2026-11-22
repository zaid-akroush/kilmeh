"""Gaming attempt for rtl-react-chat: only dist/app.js is edited.

Runs in the app directory on top of the untouched fixture.
"""

from pathlib import Path

path = Path("dist/app.js")
path.write_text(
    path.read_text(encoding="utf-8")
    + "\ndocument.documentElement.lang='ar-JO';document.documentElement.dir='rtl';\n",
    encoding="utf-8",
)
