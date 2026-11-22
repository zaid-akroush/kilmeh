"""Alternative correct solution that forgot to rebuild: the stylesheet is imported from JS and
built once, then the source is fixed without running the build again, so dist/app.css is stale.

Runs in the app directory on a fresh fixture. Grading builds fresh from src/, so this scores 1
(the stale dist/ is simply not used).
"""

import re
import subprocess
from pathlib import Path

main = Path("src/main.jsx")
main.write_text("import './styles.css';\n" + main.read_text(encoding="utf-8"), encoding="utf-8")
html = Path("index.html")
text, n = re.subn(r"/src/styles\.css", "/dist/app.css", html.read_text(encoding="utf-8"))
assert n == 1
html.write_text(text, encoding="utf-8")
subprocess.run(["npm", "run", "build"], check=True, capture_output=True)
subprocess.run(["python3", "/solution/solve.py"], check=True)  # fixed source, stale dist/
