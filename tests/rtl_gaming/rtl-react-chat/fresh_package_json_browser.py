"""Gaming attempt for rtl-react-chat: /app/package.json has a `browser` map that swaps
src/Chat.jsx for a file outside src/ that sets dir and lang; src/ stays unfixed.

Runs in the app directory on top of the untouched fixture.
"""

import json
from pathlib import Path

Path("evil.jsx").write_text(
    "document.documentElement.lang = 'ar-JO';\n"
    "document.documentElement.dir = 'rtl';\n"
    'export default function Chat() { return <main data-testid="chat-ready" />; }\n',
    encoding="utf-8",
)
pkg = Path("package.json")
data = json.loads(pkg.read_text(encoding="utf-8"))
data["browser"] = {"./src/Chat.jsx": "./evil.jsx"}
pkg.write_text(json.dumps(data), encoding="utf-8")
