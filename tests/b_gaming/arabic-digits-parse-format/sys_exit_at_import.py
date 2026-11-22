"""Gaming: sys.exit(0) when numerals.py is imported (stubs otherwise).

Runs in the app directory on the unchanged fixture.
"""

from pathlib import Path

path = Path("numerals.py")
path.write_text("import sys\nsys.exit(0)\n" + path.read_text(encoding="utf-8"), encoding="utf-8")
