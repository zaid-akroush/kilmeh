# Requirements

The directory `/app` is a small Python project. `contacts.py` holds a list of `{"id", "name", "city"}` records, and `search.py` has three stub functions: `normalize_for_search`, `search` and `sort_names`. Implement all three in `search.py`.

Use only the Python standard library: the grader imports your module without site-packages. It runs your code as an unprivileged user that cannot write to `/app` or read the grader, so don't write files at import time. `README.md` has four examples; the grader uses many more inputs than these.

## `normalize_for_search(s: str) -> str`

Return a `str` (exactly that type) that is `s` with exactly these changes, and no others:

1. Remove every character in U+0600 to U+06FF whose Unicode general category is `Mn` (nonspacing mark). In Python 3.12 (Unicode 15.0) these are U+0610 to U+061A, U+064B to U+065F, U+0670, U+06D6 to U+06DC, U+06DF to U+06E4, U+06E7 to U+06E8 and U+06EA to U+06ED. They include the tashkeel (U+064B to U+0652), U+0653 to U+0655 (maddah and hamza marks), the superscript alef U+0670 and the Quranic marks. Characters outside U+0600 to U+06FF are never removed, even if they are `Mn` (a Latin `e` followed by U+0301 keeps its U+0301). Characters inside the block that are not `Mn` stay (U+06E5 and U+06E6 are letters, U+06DD and U+061C are format characters).
2. Remove tatweel (U+0640).
3. Map alef with hamza above (U+0623), alef with hamza below (U+0625), alef with madda (U+0622) and alef wasla (U+0671) to plain alef (U+0627); taa marbuta (U+0629) to haa (U+0647); alef maqsura (U+0649) to yaa (U+064A).
4. Apply `str.casefold()` to the result, so Latin letters fold (`"Straße"` gives `"strasse"`). Everything else, spaces included, is kept.

It does not change anything else. In particular, these stay exactly as they are: waw with hamza (U+0624), yaa with hamza (U+0626), hamza (U+0621), the ligature U+FDF2 (not expanded to its letters), and Persian and Urdu letters (U+067E, U+0686, U+0698, U+06A9, U+06AF, U+06CC and so on). Don't apply Unicode normalization (NFC, NFD, NFKC or NFKD) to the whole string: it would break U+FDF2 and turn U+0624 and U+0626 into plain letters.

Input may be precomposed (U+0623) or decomposed (U+0627 followed by U+0654). Both come out as U+0627, because U+0654 is removed by rule 1. A decomposed waw with hamza (U+0648 U+0654) therefore comes out as plain waw (U+0648), while the precomposed U+0624 stays U+0624.

## `search(records: list[dict], query: str) -> list[dict]`

Normalize the query with `normalize_for_search`. A record matches when that normalized query is a substring of the normalized `name` or of the normalized `city`. Normalize both sides the same way. Return a list of the matching records in their input order, and return the original record objects themselves: the same objects that are in `records`, not copies, with their `name` and `city` unchanged. `search` must not modify `records` or any record in it in any way (no new keys, no rewritten values, no re-ordering). If the query is empty after normalizing (for example `""`, or only tashkeel and tatweel), return `[]`.

## `sort_names(names: list[str]) -> list[str]`

Return a new list of the same strings, ordered by the key `(normalize_for_search(name), name)`: first by the normalized form, then, for names with the same normalized form, by the original string. Compare strings by code point (Python's normal string order). Return the original strings, not their normalized forms, and keep duplicates. Don't use `locale`: no Arabic locale is installed.
