"""Mutation: sort_names returns the normalized strings, in the right order.

Runs in the app directory on top of the reference solution.
Only the originals check fails (order is graded on normalized form).
"""

from pathlib import Path

Path("search.py").open("a", encoding="utf-8").write("""

_real_search = search
_real_norm = normalize_for_search
def sort_names(names):
    return [_real_norm(n) for n in sorted(names, key=lambda n: (_real_norm(n), n))]
""")
