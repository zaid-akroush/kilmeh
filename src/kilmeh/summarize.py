"""`kilmeh summarize-run <jobs_dir>`: markdown pass rates from Harbor trial folders.

Layout read: <jobs>/<job>/<trial>/{result.json, verifier/reward.txt}. A trial with no
reward counts as a fail, unless result.json records a Harbor exception (an infra error such
as NetworkConnectionError): then it is counted under `errors` and left out of the pass-rate
denominator. A trial whose result.json records `AgentTimeoutError` and that has a reward
is still graded by its reward; it is also counted under `timeouts` (informational only).
Every file under the jobs dir is scanned for token-like strings
first; if one is found nothing is printed except the file name (never the match).
Parity = pass rate of a non-en variant / pass rate of the same task's en variant; a task's
track is the folder holding it under the tasks dir (`<tasks>/<track>/<task-id>/`).
"""

import json
import math
import re
from collections import defaultdict
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

TOKEN_PATTERNS = {
    "anthropic key or OAuth token": re.compile(rb"sk-ant-[\w-]{10,}"),
    "sk- key": re.compile(rb"(?<![A-Za-z0-9])sk-[\w-]{20,}"),
    "lowercase-hex sk- key": re.compile(rb"(?<![A-Za-z0-9])sk-[0-9a-f]{32,}"),
    "Hugging Face token": re.compile(rb"(?<![A-Za-z0-9])hf_[A-Za-z0-9]{30,}"),
    "JWT": re.compile(rb"eyJ[\w-]{8,}\.[\w-]{8,}\."),
}
# `\/` is a JSON-escaped `/`, so escaped base64 keys still form one run.
# ponytail: a bare `/` would flag real trial paths; a 40+ char blob split by bare `/` slips by
_LONG = re.compile(rb"(?:[A-Za-z0-9+_-]|\\/){40,}={0,2}")
LOOP_TASK = "loop-for-to-while"
LOOP_VARIANTS = ("en", "levantine", "arabizi_levantine")


def _looks_base64(s: bytes) -> bool:
    # ponytail: needs upper, lower and digit; lowercase hex checksums and paths pass
    return (
        re.search(rb"[a-z]", s) is not None
        and re.search(rb"[A-Z]", s) is not None
        and re.search(rb"[0-9]", s) is not None
    )


def find_leaks(root: Path) -> list[str]:
    """`path: kind` for each file holding a token-like string."""
    leaks = []
    paths = sorted(root.rglob("*"))
    # Harbor trial dir names (`<task>__<random>`) can look like base64; blank them for _LONG only.
    # A space, not b"", so the text on either side can't join into one long run.
    # Only names that are long runs themselves: blanking `11` (sessions/2026/11/) would split blobs.
    names = {n for p in paths if _LONG.fullmatch(n := p.name.encode())}
    for f in (p for p in paths if p.is_file()):
        data = f.read_bytes()
        kinds = [k for k, rx in TOKEN_PATTERNS.items() if rx.search(data)]
        unnamed = data
        for name in names:
            unnamed = unnamed.replace(name, b" ")
        if any(_looks_base64(m.group()) for m in _LONG.finditer(unnamed)):
            kinds.append("long base64")
        if kinds:
            leaks.append(f"{f}: {', '.join(kinds)}")
    return leaks


def _load(res: Path) -> dict:
    r = json.loads(res.read_text(encoding="utf-8"))
    d = res.parent
    info = r.get("agent_info") or {}
    model = (info.get("model_info") or {}).get("name")
    try:
        reward = float((d / "verifier" / "reward.txt").read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        reward = None
    exc = (r.get("exception_info") or {}).get("exception_type")
    errored = reward is None and r.get("exception_info") is not None
    timeout = not errored and exc == "AgentTimeoutError"  # errored: no usable reward
    return {
        "r": r,
        "dir": d,
        "agent": f"{info.get('name')}/{model}" if model else str(info.get("name")),
        "name": info.get("name"),
        "model": model,
        "reward": reward,
        "passed": reward is not None and reward >= 1,
        "errored": errored,
        "timeout": timeout,
        "variant": r["task_name"].removeprefix("kilmeh/"),
    }


CAUSES = ("setup_timeout", "agent_timeout", "harness_error", "tests_failed")
# ponytail: no_change is not detectable, Harbor 0.25 saves no workspace diff (RESULTS_FORMAT.md)
_SETUP_EXC = re.compile(r"AgentSetupTimeoutError|EnvironmentStart|Build")


def failure_cause(t: dict) -> str | None:
    """None for a pass; else the first matching cause in CAUSES order."""
    if t["passed"]:
        return None
    exc = (t["r"].get("exception_info") or {}).get("exception_type")
    if exc and _SETUP_EXC.search(exc):
        return "setup_timeout"
    if exc == "AgentTimeoutError":
        return "agent_timeout"
    if exc or t["reward"] is None:  # no reward and no exception: verifier never ran
        return "harness_error"
    return "tests_failed"


def _cause_rows(root: Path) -> dict[tuple[str, str], list[int]]:
    # [timed out, *CAUSES] per (agent, prompt-variant kind); timed out counts every trial
    rows: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0] * (len(CAUSES) + 1))
    for res in sorted(root.glob("*/*/result.json")):
        t = _load(res)
        row = rows[t["agent"], t["variant"].partition("--")[2] or "-"]
        exc = (t["r"].get("exception_info") or {}).get("exception_type")
        row[0] += exc == "AgentTimeoutError"
        cause = failure_cause(t)
        if cause:
            row[1 + CAUSES.index(cause)] += 1
    return rows


def _causes(root: Path) -> str:
    rows = _cause_rows(root)
    head = f"| agent | variant | timed out | {' | '.join(CAUSES)} |"
    lines = ["", "## Failure causes", "", head, "|---" * (len(CAUSES) + 3) + "|"]
    lines += [f"| {a} | {v} | {' | '.join(map(str, c))} |" for (a, v), c in sorted(rows.items())]
    return "\n".join(lines)


def _trials(root: Path):
    for res in sorted(root.glob("*/*/result.json")):
        t = _load(res)
        yield t["variant"], t["agent"], t["passed"], t["errored"], t["timeout"]


SCHEMA_VERSION = 1


def _json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _seconds(r: dict):
    try:
        t0, t1 = (datetime.fromisoformat(r[k]) for k in ("started_at", "finished_at"))
        return round((t1 - t0).total_seconds(), 3)
    except (KeyError, TypeError, ValueError):
        return None


def records(root: Path) -> list[dict]:
    """One dict per trial, for `--jsonl`. Format: docs/RESULTS_FORMAT.md."""
    out = []
    for res in sorted(root.glob("*/*/result.json")):
        t = _load(res)
        r, d = t["r"], t["dir"]
        ar = r.get("agent_result") or {}
        traj = d / "agent" / "trajectory.json"
        fm = (_json(traj) or {}).get("final_metrics") or {}
        # result.json first; the trajectory's final_metrics fill what it lacks
        usage = {
            "input_tokens": _first(ar.get("n_input_tokens"), fm.get("total_prompt_tokens")),
            "cached_tokens": _first(ar.get("n_cache_tokens"), fm.get("total_cached_tokens")),
            "output_tokens": _first(ar.get("n_output_tokens"), fm.get("total_completion_tokens")),
            "cost_usd": _first(ar.get("cost_usd"), fm.get("total_cost_usd")),
        }
        task, sep, variant = t["variant"].partition("--")
        if t["errored"]:
            status = "error"
        elif t["timeout"]:
            status = "timeout"
        else:
            status = "passed" if t["passed"] else "failed"

        def rel(p: Path):
            return p.relative_to(root).as_posix() if p.is_file() else None

        out.append(
            {
                "schema_version": SCHEMA_VERSION,
                "task_id": task,
                "prompt_variant": variant if sep else None,
                "agent": t["name"],
                "model": t["model"],
                "trial_id": r.get("trial_name", d.name),
                "reward": t["reward"],
                "status": status,
                "checks": _json(d / "verifier" / "checks.json"),
                **usage,
                "duration_sec": _seconds(r),
                "transcript": rel(traj),
                "verify_log": rel(d / "verifier" / "verify.log"),
                "failure_cause": failure_cause(t),
                "diff": None,  # Harbor 0.25 saves no diff; see docs/RESULTS_FORMAT.md
            }
        )
    return out


def _first(*vals):
    return next((v for v in vals if v is not None), None)


def write_jsonl(root: Path, out: Path) -> int:
    recs = records(root)
    lines = "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in recs)
    out.write_text(lines, encoding="utf-8", newline="\n")
    return len(recs)


def _rate(passed: int, graded: int) -> str:
    if not graded:
        return "-"
    pct = (Decimal(100 * passed) / graded).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return f"{pct}%"


def _wilson(passed: int, graded: int) -> str:
    """95% Wilson score interval for passed/graded, whole percents like `12–71%`."""
    if not graded:
        return "-"
    z, p = 1.96, passed / graded
    d = 1 + z * z / graded
    mid = (p + z * z / (2 * graded)) / d
    half = z * math.sqrt(p * (1 - p) / graded + z * z / (4 * graded**2)) / d
    return f"{math.floor((mid - half) * 100 + 0.5)}–{math.floor((mid + half) * 100 + 0.5)}%"


def _mcnemar(b: int, c: int) -> float:
    """Two-sided exact McNemar p: binomial(b + c, 1/2) on the discordant pairs."""
    n = b + c
    if not n:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2**n
    return min(1.0, 2 * tail)


def _paired_rows(root: Path, track: dict[str, str]) -> dict[tuple[str, str], list[int]]:
    # Harbor trial names carry no try index, so each task is compared on its majority
    # over graded tries (a tie, e.g. 1 of 2, counts as a fail); errored trials are left out.
    tries: dict[tuple[str, str, str], list[bool]] = defaultdict(list)
    for variant, agent, passed, errored, _ in _trials(root):
        task, _, lang = variant.partition("--")
        if not errored and track.get(task) == "a-prompts":
            tries[agent, task, lang].append(passed)
    # [both pass, en only, variant only, both fail, tasks] per (agent, variant kind); "all" pools
    rows: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0] * 5)
    for (agent, task, lang), ts in sorted(tries.items()):
        en = tries.get((agent, task, "en"))
        if lang in ("en", "") or not en:
            continue
        e, v = sum(en) * 2 > len(en), sum(ts) * 2 > len(ts)
        for kind in (lang, "all"):
            r = rows[agent, kind]
            r[{(1, 1): 0, (1, 0): 1, (0, 1): 2, (0, 0): 3}[e, v]] += 1
            r[4] += 1
    return rows


def _paired(root: Path, track: dict[str, str]) -> str:
    rows = _paired_rows(root, track)
    lines = ["", "## Paired vs English (Track A)", ""]
    lines += [
        "| agent | variant | both pass | en only | variant only | both fail | tasks | McNemar p |"
    ]
    lines += ["|---" * 8 + "|"]
    for (agent, kind), r in sorted(rows.items()):
        # pooled variants of one task are not independent, so no p there
        p = "-" if kind == "all" else f"{_mcnemar(r[1], r[2]):.3f}"
        lines.append(f"| {agent} | {kind} | {' | '.join(map(str, r))} | {p} |")
    return "\n".join(lines)


def _ratio(pa: int, ga: int, pe: int, ge: int) -> str:
    """(pa/ga) / (pe/ge) to 2 decimals, half-up; `-` when either rate is undefined or en is 0."""
    if not (ga and ge and pe):
        return "-"
    return str((Decimal(pa * ge) / (ga * pe)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _stats(roots: list[Path]) -> dict[tuple[str, str], list[int]]:
    """[trials, passed, errors, timeouts] per (variant, agent) over all roots."""
    stats: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0, 0, 0])
    for root in roots:
        for variant, agent, passed, errored, timeout in _trials(root):
            row = stats[variant, agent]
            row[0] += 1
            row[1] += passed
            row[2] += errored
            row[3] += timeout
    return stats


def summarize(root: Path, tasks: Path = Path("tasks")) -> str:
    stats = _stats([root])  # pass rate = passed / (trials - errors)
    if not stats:
        raise ValueError(f"no trials found under {root}")
    lines = [
        "| task variant | agent | trials | errors | timeouts | passed | pass rate | 95% CI |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for (variant, agent), (n, p, e, t) in sorted(stats.items()):
        row = f"| {variant} | {agent} | {n} | {e} | {t} | {p} |"
        lines.append(f"{row} {_rate(p, n - e)} | {_wilson(p, n - e)} |")
    lines += ["", f"## {LOOP_TASK}: English vs Levantine vs Arabizi", ""]
    lines += [f"| agent | {' | '.join(LOOP_VARIANTS)} |", "|---" * (len(LOOP_VARIANTS) + 1) + "|"]
    for agent in sorted({a for _, a in stats}):
        cells = []
        for v in LOOP_VARIANTS:
            s = stats.get((f"{LOOP_TASK}--{v}", agent))
            cells.append(f"{s[1]}/{s[0] - s[2]}" if s else "-")
        lines.append(f"| {agent} | {' | '.join(cells)} |")

    track = {d.name: d.parent.name for d in tasks.glob("*/*") if d.is_dir()}
    langs: dict[tuple[str, str], dict[str, tuple[int, int]]] = defaultdict(dict)
    for (variant, agent), (n, p, e, _) in stats.items():
        task, _, lang = variant.partition("--")
        langs[agent, task][lang] = (p, n - e)
    # [non-en passed, non-en graded, en passed, en graded] per (agent, track)
    pooled: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0, 0, 0])
    lines += ["", "## Parity vs English (pass rate / en pass rate)", ""]
    lines += ["| agent | task variant | parity |", "|---|---|---|"]
    for (agent, task), by_lang in sorted(langs.items()):
        if "en" not in by_lang or len(by_lang) < 2:
            continue
        pe, ge = by_lang.pop("en")
        t = pooled[agent, track.get(task, "unknown")]
        t[2] += pe
        t[3] += ge
        for lang, (pa, ga) in sorted(by_lang.items()):
            lines.append(f"| {agent} | {task}--{lang} | {_ratio(pa, ga, pe, ge)} |")
            t[0] += pa
            t[1] += ga
    lines += ["", "## Parity vs English per track (pooled)", ""]
    lines += ["| agent | track | parity |", "|---|---|---|"]
    lines += [f"| {a} | {tr} | {_ratio(*v)} |" for (a, tr), v in sorted(pooled.items())]
    return "\n".join(lines) + "\n" + _paired(root, track) + "\n" + _causes(root)
