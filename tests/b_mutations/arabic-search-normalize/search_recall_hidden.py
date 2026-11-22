"""Mutation: search drops its last match.

Runs in the app directory on top of the reference solution.
Only recall fails.
"""

from pathlib import Path

Path("search.py").open("a", encoding="utf-8").write("""

_real_search = search
_real_norm = normalize_for_search
def search(records, query):
    return _real_search(records, query)[:-1]
""")
