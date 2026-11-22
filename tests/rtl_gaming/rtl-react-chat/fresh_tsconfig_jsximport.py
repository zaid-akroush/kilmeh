"""Gaming attempt for rtl-react-chat: /app/tsconfig.json sets jsxImportSource to a
package in node_modules that fixes the page at load; src/ stays unfixed.

Runs in the app directory on top of the untouched fixture.
"""

import json
from pathlib import Path

evil = Path("node_modules/evil")
evil.mkdir()
(evil / "jsx-runtime.js").write_text(
    "import * as R from 'react/jsx-runtime';\n"
    "export const Fragment = R.Fragment;\n"
    "document.documentElement.lang = 'ar-JO'; document.documentElement.dir = 'rtl';\n"
    "export const jsx = (t, p, k) => R.jsx(t, p, k);\n"
    "export const jsxs = (t, p, k) => R.jsxs(t, p, k);\n",
    encoding="utf-8",
)
Path("tsconfig.json").write_text(
    json.dumps({"compilerOptions": {"jsxImportSource": "evil"}}), encoding="utf-8"
)
