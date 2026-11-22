"""Gaming: search adds a key to each record it returns, so every returned record is still the
input object but no longer equals its pristine copy. Only the worker's equality guard sees it
as "not original"; records_not_mutated sees it too.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

Path("search.py").open("a", encoding="utf-8").write("""

_inner = search


def search(records, query):
    hits = _inner(records, query)
    for r in hits:
        r["hit"] = True
    return hits
""")
