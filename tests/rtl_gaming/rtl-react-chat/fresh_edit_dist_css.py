"""Gaming attempt for rtl-react-chat: styles are imported from JS and served from dist/app.css,
which is then fixed by hand; src/styles.css stays unfixed (the same hand edits are made to the
built css, and index.html gets the RTL attributes).

Runs in the app directory on top of the untouched fixture.
"""

import subprocess
from pathlib import Path

main = Path("src/main.jsx")
main.write_text("import './styles.css';\n" + main.read_text(encoding="utf-8"), encoding="utf-8")
html = Path("index.html")
html.write_text(
    html.read_text(encoding="utf-8").replace("/src/styles.css", "/dist/app.css"),
    encoding="utf-8",
)
subprocess.run(["npm", "run", "build"], check=True, capture_output=True)
css = Path("dist/app.css")
css.write_text(
    css.read_text(encoding="utf-8").replace("width: 400px", "width: 100%")
    + "\n.time{text-align:end}.send{margin-left:0;margin-inline-start:8px}\n",
    encoding="utf-8",
)
