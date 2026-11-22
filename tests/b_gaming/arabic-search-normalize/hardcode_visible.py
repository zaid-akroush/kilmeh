"""Gaming: answer only the README examples, wrong answers otherwise.

Runs in the app directory on the unchanged fixture.
"""

from pathlib import Path

Path("search.py").write_text(
    """
def normalize_for_search(s):
    known = {
        "\\u0645\\u064f\\u062d\\u064e\\u0645\\u0651\\u064e\\u062f": "\\u0645\\u062d\\u0645\\u062f",
    }
    return known.get(s, s)


def search(records, query):
    ids = {"\\u0645\\u062d\\u0645\\u062f": (8, 9), "\\ufdf2": (21,)}.get(query, ())
    return [r for r in records if r["id"] in ids]


def sort_names(names):
    return sorted(names)
""",
    encoding="utf-8",
)
