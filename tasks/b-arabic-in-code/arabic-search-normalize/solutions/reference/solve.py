"""Reference search.py (solve.sh copies this file over /app/search.py).

A translate table (marks and tatweel deleted, letters folded) plus a precomputed list of the
Mn ranges inside U+0600-U+06FF (Python 3.12, Unicode 15.0). ASCII source: letters are escapes.
"""

# Mn code points in U+0600-U+06FF, as inclusive ranges.
_MN_RANGES = (
    (0x0610, 0x061A),
    (0x064B, 0x065F),
    (0x0670, 0x0670),
    (0x06D6, 0x06DC),
    (0x06DF, 0x06E4),
    (0x06E7, 0x06E8),
    (0x06EA, 0x06ED),
)
_TABLE = {c: None for lo, hi in _MN_RANGES for c in range(lo, hi + 1)}
_TABLE[0x0640] = None  # tatweel
# alef with hamza above/below, madda, wasla -> alef; taa marbuta -> haa; alef maqsura -> yaa
_TABLE.update(
    str.maketrans("\u0623\u0625\u0622\u0671\u0629\u0649", "\u0627\u0627\u0627\u0627\u0647\u064a")
)


def normalize_for_search(s: str) -> str:
    return s.translate(_TABLE).casefold()


def search(records: list[dict], query: str) -> list[dict]:
    q = normalize_for_search(query)
    if not q:
        return []
    return [
        r
        for r in records
        if q in normalize_for_search(r["name"]) or q in normalize_for_search(r["city"])
    ]


def sort_names(names: list[str]) -> list[str]:
    return sorted(names, key=lambda n: (normalize_for_search(n), n))
