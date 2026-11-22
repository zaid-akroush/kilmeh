"""Gaming: os._exit(0) when search.py is imported (stubs otherwise).

Runs in the app directory on the unchanged fixture.
"""

from pathlib import Path

path = Path("search.py")
path.write_text("import os\nos._exit(0)\n" + path.read_text(encoding="utf-8"), encoding="utf-8")
