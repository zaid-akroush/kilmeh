"""Gaming: NFKC the input first (breaks U+FDF2, folds nothing it should not keep).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

Path("search.py").open("a", encoding="utf-8").write("""

import unicodedata

_plain = normalize_for_search


def normalize_for_search(s):
    return _plain(unicodedata.normalize("NFKC", s))
""")
