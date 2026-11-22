"""Mutation: search adds a key to every record it does not return.

Runs in the app directory on top of the reference solution.
The returned records are untouched, so only the mutation check fails.
"""

from pathlib import Path

Path("search.py").open("a", encoding="utf-8").write("""

_real_search = search
_real_norm = normalize_for_search
def search(records, query):
    hits = _real_search(records, query)
    for r in records:
        if all(r is not h for h in hits):
            r['seen'] = True
    return hits
""")
