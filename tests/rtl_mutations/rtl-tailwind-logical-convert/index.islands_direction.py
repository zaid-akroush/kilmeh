"""Mutation for rtl-tailwind-logical-convert (index.html): the email island turns right-to-left; text-end keeps its text on the left.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
old = 'data-testid="email" dir="ltr" class="mt-1 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-start font-mono text-sm"'
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(
    text.replace(
        old,
        'data-testid="email" dir="rtl" class="mt-1 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-end font-mono text-sm"',
    ),
    encoding="utf-8",
)
