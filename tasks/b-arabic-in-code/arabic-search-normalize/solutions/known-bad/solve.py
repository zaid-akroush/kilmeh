"""Known-bad search.py (solve.sh copies this file over /app/search.py).

Plausible mistake: "normalize the data once". search() overwrites record["name"] with its
normalized form and returns those mutated records; sort_names() returns the normalized strings.
Matching and ordering are right. Must FAIL search_returns_originals, records_not_mutated and
sort_returns_originals, and nothing else.
"""

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
_TABLE[0x0640] = None
_TABLE.update(
    str.maketrans("\u0623\u0625\u0622\u0671\u0629\u0649", "\u0627\u0627\u0627\u0627\u0647\u064a")
)


def normalize_for_search(s: str) -> str:
    return s.translate(_TABLE).casefold()


def search(records: list[dict], query: str) -> list[dict]:
    q = normalize_for_search(query)
    if not q:
        return []
    for r in records:
        r["name"] = normalize_for_search(r["name"])
    return [r for r in records if q in r["name"] or q in normalize_for_search(r["city"])]


def sort_names(names: list[str]) -> list[str]:
    return sorted(normalize_for_search(n) for n in names)
