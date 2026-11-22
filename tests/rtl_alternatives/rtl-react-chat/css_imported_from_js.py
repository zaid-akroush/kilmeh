"""Alternative correct solution: the stylesheet is imported from main.jsx (so esbuild writes
dist/app.css) and index.html links /dist/app.css; the project is rebuilt after the fix.

Runs in the app directory on a fresh fixture. The fix itself is the reference solution's edits
(applied from /solution, mounted by the test harness); only the CSS wiring differs.
"""

import re
import subprocess
from pathlib import Path

subprocess.run(["python3", "/solution/solve.py"], check=True)

main = Path("src/main.jsx")
main.write_text("import './styles.css';\n" + main.read_text(encoding="utf-8"), encoding="utf-8")
html = Path("index.html")
text, n = re.subn(r"/src/styles\.css", "/dist/app.css", html.read_text(encoding="utf-8"))
assert n == 1
html.write_text(text, encoding="utf-8")
subprocess.run(["npm", "run", "build"], check=True, capture_output=True)
assert Path("dist/app.css").is_file()
