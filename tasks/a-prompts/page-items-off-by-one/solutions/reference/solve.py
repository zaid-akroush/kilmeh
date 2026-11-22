# Reference solution: pages start at 1.
import sys

p = sys.argv[1] if len(sys.argv) > 1 else "/app/paging.py"
new = """def get_page(items, page, per_page):
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end]
"""
with open(p, "wb") as f:
    f.write(new.encode("utf-8"))
