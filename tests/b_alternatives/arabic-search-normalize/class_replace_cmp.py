"""Alternative (b): one regex character class of explicit ranges for the deletions, a str.replace
chain for the letter maps, and a cmp_to_key sort with a hand-written comparator.

Runs in the app directory on the unchanged fixture; writes search.py.
"""

from pathlib import Path

Path("search.py").write_text(
    """
import re
from functools import cmp_to_key

_DELETE = re.compile(
    "[\\u0610-\\u061a\\u064b-\\u065f\\u0670\\u06d6-\\u06dc\\u06df-\\u06e4\\u06e7\\u06e8\\u06ea-\\u06ed\\u0640]"
)


def normalize_for_search(s):
    out = _DELETE.sub("", s)
    for old in ("\\u0623", "\\u0625", "\\u0622", "\\u0671"):
        out = out.replace(old, "\\u0627")
    return out.replace("\\u0629", "\\u0647").replace("\\u0649", "\\u064a").casefold()


def search(records, query):
    q = normalize_for_search(query)
    if not q:
        return []
    hits = []
    for r in records:
        name, city = normalize_for_search(r["name"]), normalize_for_search(r["city"])
        if name.find(q) >= 0 or city.find(q) >= 0:
            hits.append(r)
    return hits


def _compare(a, b):
    ka, kb = (normalize_for_search(a), a), (normalize_for_search(b), b)
    return (ka > kb) - (ka < kb)


def sort_names(names):
    return sorted(names, key=cmp_to_key(_compare))
""",
    encoding="utf-8",
)
