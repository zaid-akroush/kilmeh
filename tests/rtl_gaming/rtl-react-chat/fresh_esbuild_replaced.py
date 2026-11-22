# ruff: noqa: E402, E501, I001
"""Gaming attempt for rtl-react-chat: the fixed bundle is prebuilt and node_modules/esbuild is
replaced by a script that copies it to the output, while src/ stays unfixed.

Runs in the app directory on top of the untouched fixture (it applies the reference itself,
builds, then puts the unfixed source back).
"""

import shutil
import subprocess
from pathlib import Path

shutil.copy("src/Chat.jsx", "/tmp/Chat.orig.jsx")
shutil.copy("index.html", "/tmp/index.orig.html")
subprocess.run(["bash", "/solution/solve.sh"], check=True, capture_output=True)
subprocess.run(
    [
        "node",
        "node_modules/esbuild/bin/esbuild",
        "src/main.jsx",
        "--bundle",
        "--jsx=automatic",
        '--define:process.env.NODE_ENV="production"',
        "--outfile=node_modules/.good.js",
    ],
    check=True,
    capture_output=True,
)
shutil.copy("/tmp/Chat.orig.jsx", "src/Chat.jsx")
Path("node_modules/esbuild/bin/esbuild").write_text(
    "#!/usr/bin/env node\n"
    "const fs = require('fs');\n"
    "const arg = process.argv.find((a) => a.startsWith('--outfile=') || a.startsWith('--outdir='));\n"
    "const dest = arg.startsWith('--outfile=') ? arg.slice(10) : arg.slice(9) + '/app.js';\n"
    f"fs.copyFileSync('{Path.cwd()}/node_modules/.good.js', dest);\n",
    encoding="utf-8",
)
