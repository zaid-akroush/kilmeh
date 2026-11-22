"""`kilmeh results-page OUT_HTML JOBS_DIR...`: one self-contained HTML page of the results.

Numbers come from summarize.py (pass rates, Wilson CI, paired counts, failure causes); this
module only lays them out. No JS, no external requests; every string is html.escaped.
"""

import re
from collections import defaultdict
from html import escape
from pathlib import Path

from kilmeh import summarize as sm

CAVEAT = "Small local model, few tries: shows the benchmark works, not how frontier agents score."
_ARABIC = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")
CSS = """
:root{color-scheme:light dark;--bg:#fff;--fg:#1a1a1a;--mut:#666;--line:#d8d8d8;--head:#f2f2f2}
@media(prefers-color-scheme:dark){:root{--bg:#161616;--fg:#e8e8e8;--mut:#9a9a9a;--line:#3a3a3a;--head:#222}}
body{background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;margin:0 auto;
max-width:60rem;padding:0 16px 3rem}
h1{margin:1.5rem 0 .25rem}h2{margin:2rem 0 .5rem;font-size:1.2rem}
.mut{color:var(--mut)}.wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.9rem}
th,td{border:1px solid var(--line);padding:.35rem .5rem;text-align:start;white-space:nowrap}
th{background:var(--head)}
"""


def _td(v) -> str:
    text = str(v)
    attr = ' dir="auto"' if _ARABIC.search(text) else ""
    return f"<td{attr}>{escape(text)}</td>"


def _table(head: list[str], rows: list[list]) -> str:
    th = "".join(f"<th>{escape(h)}</th>" for h in head)
    body = "".join("<tr>" + "".join(_td(c) for c in r) + "</tr>" for r in rows)
    return f'<div class="wrap"><table><tr>{th}</tr>{body}</table></div>'


def _cell(p: int, g: int) -> str:
    return f"{p}/{g} ({sm._rate(p, g)}, CI {sm._wilson(p, g)})" if g else "-"


def _merge(into: dict, add: dict) -> None:
    for k, v in add.items():
        into[k] = [a + b for a, b in zip(into[k], v, strict=True)] if k in into else list(v)


def _dates(roots: list[Path]) -> str:
    days = sorted(
        str((sm._json(r) or {}).get("started_at") or "")[:10]
        for root in roots
        for r in root.glob("*/*/result.json")
    )
    days = [d for d in days if d]
    return f"{days[0]} to {days[-1]}" if days else "unknown"


def render(roots: list[Path], tasks: Path = Path("tasks"), title: str = "Kilmeh results") -> str:
    stats = sm._stats(roots)
    if not stats:
        raise ValueError("no trials found under " + ", ".join(map(str, roots)))
    track = {d.name: d.parent.name for d in tasks.glob("*/*") if d.is_dir()}
    paired: dict = {}
    causes: dict = {}
    for root in roots:
        _merge(paired, sm._paired_rows(root, track))
        _merge(causes, sm._cause_rows(root))
    agents = sorted({a for _, a in stats})

    def total(keep) -> dict[str, list[int]]:  # agent -> [passed, graded]
        out: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for (variant, agent), (n, p, e, _) in stats.items():
            if keep(variant.partition("--")[0]):
                out[agent][0] += p
                out[agent][1] += n - e
        return out

    overall = total(lambda _: True)
    sections = [
        (
            "Overall pass rate per agent",
            _table(
                ["agent / model", "passed", "graded", "pass rate", "95% CI"],
                [[a, *overall[a], sm._rate(*overall[a]), sm._wilson(*overall[a])] for a in agents],
            ),
        )
    ]
    rows = []
    for t in sorted({track.get(v.partition("--")[0], "unknown") for v, _ in stats}):
        by_agent = total(lambda task, t=t: track.get(task, "unknown") == t)
        rows += [[a, t, *pg, sm._rate(*pg), sm._wilson(*pg)] for a, pg in sorted(by_agent.items())]
    sections.append(
        (
            "Per track",
            _table(["agent / model", "track", "passed", "graded", "pass rate", "95% CI"], rows),
        )
    )

    langs = list(sm.LOOP_VARIANTS) + sorted(
        {v.partition("--")[2] for v, _ in stats} - set(sm.LOOP_VARIANTS) - {""}
    )
    grid: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    for (variant, agent), (n, p, e, _) in stats.items():
        task, _, lang = variant.partition("--")
        grid[agent, task][lang or "-"] = _cell(p, n - e)
    sections.append(
        (
            "Per task and prompt language",
            _table(
                ["agent / model", "task", *langs],
                [[a, t, *(by.get(lg, "-") for lg in langs)] for (a, t), by in sorted(grid.items())],
            ),
        )
    )

    paired_head = ["agent / model", "variant", "both pass", "en only", "variant only", "both fail"]
    sections.append(
        (
            "Track A: paired vs English",
            _table(
                [*paired_head, "tasks", "McNemar p"],
                [
                    [a, k, *r, "-" if k == "all" else f"{sm._mcnemar(r[1], r[2]):.3f}"]
                    for (a, k), r in sorted(paired.items())
                ],
            ),
        )
    )
    sections.append(
        (
            "Failure causes",
            _table(
                ["agent / model", "variant", "timed out", *sm.CAUSES],
                [[a, v, *c] for (a, v), c in sorted(causes.items())],
            ),
        )
    )

    body = "".join(f"<section><h2>{escape(h)}</h2>{t}</section>" for h, t in sections)
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{escape(title)}</title><style>{CSS}</style></head><body>"
        f"<header><h1>{escape(title)}</h1>"
        f'<p class="mut">Runs: {escape(_dates(roots))}. '
        f"Agents and models: {escape(', '.join(agents))}.</p>"
        f"<p><strong>{escape(CAVEAT)}</strong></p></header>{body}</body></html>\n"
    )
