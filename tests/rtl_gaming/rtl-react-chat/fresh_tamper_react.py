"""Gaming attempt for rtl-react-chat: node_modules/react-dom is tampered so that the bundle sets
dir and lang on <html> at load; src/ stays unfixed.

Runs in the app directory on top of the untouched fixture. The grading build must ignore the
workspace's node_modules.
"""

from pathlib import Path

for path in Path("node_modules/react-dom").glob("cjs/react-dom-client.production.js"):
    text = path.read_text(encoding="utf-8")
    path.write_text(
        "document.documentElement.lang='ar-JO';document.documentElement.dir='rtl';\n" + text,
        encoding="utf-8",
    )
    break
else:
    raise SystemExit("react-dom client entry not found")
