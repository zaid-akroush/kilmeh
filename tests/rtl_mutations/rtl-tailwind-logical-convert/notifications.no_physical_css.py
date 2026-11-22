"""Mutation for rtl-tailwind-logical-convert (notifications.html): the webhook island gets text-align: left through a variable (computed pass only, so the shared CSS fails this page alone).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("notifications.html")
text = path.read_text(encoding="utf-8")
old = 'data-testid="webhook" dir="ltr" class="block break-all rounded-md bg-slate-900 px-3 py-2 text-start text-sm text-slate-100"'
assert text.count(old) == 1, "reference changed: update this mutation"
path.write_text(
    text.replace(
        old,
        'data-testid="webhook" dir="ltr" class="block break-all rounded-md bg-slate-900 px-3 py-2 [--side:left] [text-align:var(--side)] text-sm text-slate-100"',
    ),
    encoding="utf-8",
)
