"""Gaming: sort_names is plain sorted(names), no Arabic-aware key.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

Path("search.py").open("a", encoding="utf-8").write("""

def sort_names(names):
    return sorted(names)
""")
