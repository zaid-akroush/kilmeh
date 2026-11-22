"""Mutation: taa marbuta U+0629 is not mapped to haa.

Runs in the app directory on top of the reference solution.
Only the exported normalize_for_search is broken (search and sort keep the real one), so
only its direct check fails.
"""

from pathlib import Path

Path("search.py").open("a", encoding="utf-8").write("""

_real = normalize_for_search


def search(records, query):
    q = _real(query)
    if not q:
        return []
    return [r for r in records if q in _real(r["name"]) or q in _real(r["city"])]


def sort_names(names):
    return sorted(names, key=lambda n: (_real(n), n))


_BAD = dict(_TABLE)
del _BAD[0x0629]


def normalize_for_search(s):
    return s.translate(_BAD).casefold()
""")
