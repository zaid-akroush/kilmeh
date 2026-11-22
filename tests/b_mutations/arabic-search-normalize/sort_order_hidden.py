"""Mutation: sort_names is plain sorted(names).

Runs in the app directory on top of the reference solution.
It returns the original strings, in the wrong order.
"""

from pathlib import Path

Path("search.py").open("a", encoding="utf-8").write("""

_real_search = search
_real_norm = normalize_for_search
def sort_names(names):
    return sorted(names)
""")
