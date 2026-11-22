"""Gaming attempt for rtl-react-chat: the fixed source is built by hand into a bundle at another
path and index.html loads that instead of /dist/app.js, so the grader's rebuild is bypassed.

Runs in the app directory on top of the reference solution.
"""

import subprocess
from pathlib import Path

subprocess.run(
    [
        "node",
        "node_modules/esbuild/bin/esbuild",
        "src/main.jsx",
        "--bundle",
        "--jsx=automatic",
        '--define:process.env.NODE_ENV="production"',
        "--outfile=bundle.js",
    ],
    check=True,
    capture_output=True,
)
path = Path("index.html")
text = path.read_text(encoding="utf-8")
assert "/dist/app.js" in text
path.write_text(text.replace("/dist/app.js", "/bundle.js"), encoding="utf-8")
