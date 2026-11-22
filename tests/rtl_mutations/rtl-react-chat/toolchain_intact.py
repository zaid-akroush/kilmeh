"""Mutation for rtl-react-chat: a file of the grading toolchain under /opt is changed.

Runs (as root, in the test container) on top of the reference solution. A comment appended to
react/index.js does not change what the bundle does, so only the integrity check fails. The test
harness restores /opt/kilmeh-build before each case.
"""

from pathlib import Path

with Path("/opt/kilmeh-build/node_modules/react/index.js").open("a", encoding="utf-8") as f:
    f.write("\n// tampered\n")
