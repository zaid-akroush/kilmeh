"""Mutation for rtl-tailwind-logical-convert (billing.html): one graded element uses rtl:/ltr: logical variants that do not mirror (LTR unchanged).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("billing.html")
text = path.read_text(encoding="utf-8")
old = "absolute start-0 "
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(text.replace(old, "absolute ltr:start-0 rtl:end-0 "), encoding="utf-8")
