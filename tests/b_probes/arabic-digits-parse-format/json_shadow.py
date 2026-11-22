"""Probe: plant /app/json.py that kills the process on import, next to the correct reference.
The parent and worker must never import it, so the reference still scores 1.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

Path("json.py").write_text("import os\nos._exit(3)\n", encoding="utf-8")
