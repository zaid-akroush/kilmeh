# Known-bad solution: shifts the start by one item instead of one page.
import sys

p = sys.argv[1] if len(sys.argv) > 1 else "/app/paging.py"
new = """def get_page(items, page, per_page):
    start = page * per_page - 1
    end = start + per_page
    return items[start:end]
"""
with open(p, "wb") as f:
    f.write(new.encode("utf-8"))
