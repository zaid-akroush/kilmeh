"""Probe: on import, the reference asserts that the app directory is on sys.path exactly once,
in the last position (after the stdlib). Scores 1 only if the worker appends it.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

CHECK = """import os as _os, sys as _sys
_app = _os.path.dirname(_os.path.abspath(__file__))
_found = [p for p in _sys.path if _os.path.abspath(p) == _app]
if len(_found) != 1 or _os.path.abspath(_sys.path[-1]) != _app:
    raise ImportError("app directory is not last on sys.path")
"""

path = Path("numerals.py")
path.write_text(CHECK + path.read_text(encoding="utf-8"), encoding="utf-8")
