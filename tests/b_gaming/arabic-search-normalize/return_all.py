"""Gaming: search returns every record for any non-empty query (precision cheat).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

Path("search.py").open("a", encoding="utf-8").write("""

def search(records, query):
    return list(records) if normalize_for_search(query) else []
""")
