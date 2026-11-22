"""Mutation: search adds one unrelated record (the first non-match) whenever there is a
match, in input order.

Runs in the app directory on top of the reference solution.
Only precision fails.
"""

from pathlib import Path

Path("search.py").open("a", encoding="utf-8").write("""

_real_search = search
_real_norm = normalize_for_search
def search(records, query):
    ids = {r['id'] for r in _real_search(records, query)}
    extra = next((r['id'] for r in records if r['id'] not in ids), None)
    return [r for r in records if r['id'] in ids or (ids and r['id'] == extra)]
""")
