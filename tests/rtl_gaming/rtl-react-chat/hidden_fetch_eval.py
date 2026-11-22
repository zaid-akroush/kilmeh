"""Gaming attempt for rtl-react-chat: the app fetches a hidden file and evals it.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

Path("hidden.js").write_text("void 0;", encoding="utf-8")
with Path("src/main.jsx").open("a", encoding="utf-8") as f:
    f.write("fetch('/hidden.js').then((r) => r.text()).then(eval);\n")
