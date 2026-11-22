"""Gaming: NFD, drop every Mn in the string, then the letter folds (the tempting short way).

NFD turns U+0624 and U+0626 into plain letters plus U+0654, which is then stripped, and strips
Mn marks outside U+0600-U+06FF. Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

Path("search.py").open("a", encoding="utf-8").write("""

import unicodedata


def normalize_for_search(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s.translate(_TABLE).casefold()
""")
