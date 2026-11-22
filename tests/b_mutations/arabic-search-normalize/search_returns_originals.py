"""Mutation: search returns copies of the matching records.

Runs in the app directory on top of the reference solution.
Only the originals check fails.
"""

from pathlib import Path

Path("search.py").open("a", encoding="utf-8").write("""

_real_search = search
_real_norm = normalize_for_search
def search(records, query):
    return [dict(r) for r in _real_search(records, query)]
""")
