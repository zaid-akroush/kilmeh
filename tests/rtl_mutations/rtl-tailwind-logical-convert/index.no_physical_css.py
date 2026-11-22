"""Mutation for rtl-tailwind-logical-convert (index.html): the email island gets text-align: left through a variable (computed pass only, so the shared CSS fails this page alone).

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
        'data-testid="email" dir="ltr" class="mt-1 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 [--side:left] [text-align:var(--side)] font-mono text-sm"',
    ),
    encoding="utf-8",
)
