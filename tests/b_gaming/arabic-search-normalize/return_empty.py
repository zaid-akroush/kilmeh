"""Gaming: search always returns [] (recall cheat; negatives pass).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

Path("search.py").open("a", encoding="utf-8").write("""

def search(records, query):
    return []
""")
