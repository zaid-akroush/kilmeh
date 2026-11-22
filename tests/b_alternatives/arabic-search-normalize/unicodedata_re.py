"""Alternative (a): `unicodedata.category(c) == "Mn"` inside U+0600-U+06FF, then re.sub for the
letter maps. No precomputed table.

Runs in the app directory on the unchanged fixture; writes search.py.
"""

from pathlib import Path

Path("search.py").write_text(
    """
import re
import unicodedata


def normalize_for_search(s):
    s = "".join(
        c
        for c in s
        if c != "\\u0640" and not ("\\u0600" <= c <= "\\u06ff" and unicodedata.category(c) == "Mn")
    )
    s = re.sub("[\\u0623\\u0625\\u0622\\u0671]", "\\u0627", s)
    s = re.sub("\\u0629", "\\u0647", s)
    s = re.sub("\\u0649", "\\u064a", s)
    return s.casefold()


def search(records, query):
    q = normalize_for_search(query)
    if q == "":
        return []
    result = []
    for r in records:
        if q in normalize_for_search(r["name"]) or q in normalize_for_search(r["city"]):
            result.append(r)
    return result


def sort_names(names):
    return sorted(names, key=lambda n: (normalize_for_search(n), n))
""",
    encoding="utf-8",
)
