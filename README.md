<p align="center">
  <img src=".github/banner.png" alt="Kilmeh" width="720">
</p>

<h3 align="center">An open benchmark for coding agents on Arabic</h3>

<p align="center">
  Arabic prompts · Arabic text in code · right-to-left UI
</p>

<p align="center">
  <a href="docs/ROADMAP.md">Roadmap</a> ·
  <a href="tasks/SCHEMA.md">Task format</a> ·
  <a href="docs/MARKET_RESEARCH.md">Research</a> ·
  <a href="https://kilmeh.github.io/contribute">Contribute words</a>
</p>

---

# Kilmeh (كلمة)

> *Kilmeh* means "word" in Arabic.

**Kilmeh tests whether AI coding agents can build software for Arabic users:** Jordanian and Arabizi prompts, Arabic text kept byte-for-byte through code edits, and right-to-left (RTL) UIs checked in a real browser, with no AI judge.

**Status:** v1.0 in progress: 19 tasks with deterministic graders, and a first run of Claude Code and Codex on a small local model ([`results/v1-run-2026-11.md`](results/v1-run-2026-11.md)). These runs show the benchmark works end to end; they are not findings about frontier agents. No leaderboard yet. The prompts are written or approved by one native Jordanian speaker; a full native review is planned for v1.1. See [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Progress

Updated 2026-11-22. Target: v1.0, Jordanian only (Jordanian Arabic and Jordanian Arabizi, no MSA), local models only, no budget. Detail in [`docs/ROADMAP.md`](docs/ROADMAP.md).

| Feature | What it does | Status |
|---|---|---|
| Task format and validator | One schema for every task; `kilmeh validate-tasks` | ✅ Done |
| Self-test in CI | Proves every task's reference passes and its known-bad fails, on every change | ✅ Done |
| Harbor export | Turns tasks into Harbor / Terminal-Bench folders | ✅ Done |
| RTL grader | Checks right-to-left pages in a real browser, no AI judge | ✅ Done |
| Cheat-resistant graders | Random inputs each run; quitting early or faking output scores 0 | ✅ Done for all 6 Arabic-in-code tasks |
| Contributor website | Native speakers submit Arabizi spellings | ✅ Live |
| Track A: Arabic prompts | Same task in English, Jordanian and Jordanian Arabizi | ✅ 4 (all three versions written or approved by a native speaker) |
| Track B: Arabic inside code | Digits, search, bytes, files, currency | ✅ 6 |
| Track C: right-to-left UI | Layouts, Tailwind, React, mixed Arabic/English text | ✅ 6 (English and Jordanian prompts) + 3 mixed-text tasks for v1.1 (English prompts) |
| Arabizi spelling map | Shows how Jordanians spell each word in Latin letters | 🟦 Design approved, building next |
| First results and release | Run agents, publish scores | 🟨 v1.0 run done (Claude Code and Codex, local 9B model): [`results/v1-run-2026-11.md`](results/v1-run-2026-11.md). Release pending. |

**Coming next:** v1.0 release (Jordanian only, local models). Then v1.1: the three mixed Arabic and English text (bidi) tasks (built, PR #86), the native speaker's review of every prompt, Jordanian Arabizi for Tracks B and C, and the strict release check.

## Why

Existing Arabic LLM benchmarks (3LM, QIMMA, ArabicMMLU) test knowledge and function-level code generation. Existing agentic coding benchmarks (SWE-bench and its multilingual variants) vary the *programming* language, not the *natural* language. LILT's multilingual terminal benchmarks include some Arabic tasks (a few open, most held out). No one measures agents on right-to-left UI, Arabic dialect and Arabizi prompts, or keeping Arabic bytes intact through edits. See [`docs/MARKET_RESEARCH.md`](docs/MARKET_RESEARCH.md).

## What it measures

| Track | Question | Example check |
|---|---|---|
| **A. Arabic prompts** | Does task success hold when the instruction is in Jordanian Arabic or Jordanian Arabizi (Arabic typed in Latin letters and digits) instead of English? (v1.0 ships no MSA.) | Same task, N phrasings, compare pass rate to the English baseline |
| **B. Arabic in code** | Are Arabic comments, strings, identifiers and filenames preserved? | Byte-exact check, Unicode normalization, no transliteration or reordering |
| **C. RTL UI** | Does generated or edited UI work right-to-left? | Computed `direction`, logical CSS properties, no double-flip, bounding-box position checks via Playwright |
| **D. Output language** (planned, no tasks yet) | Does the agent answer, comment and write commits in the language requested? | Language-ID on responses and diffs |

## Principles

- **Deterministic first.** Pass/fail from tests and DOM or computed-style assertions. A VLM judge is a later, secondary signal.
- **Native tasks.** Tasks are authored or reviewed by native speakers. Dialect and Arabizi prompts are never machine-written alone. See [`tasks/REVIEW_PROCESS.md`](tasks/REVIEW_PROCESS.md).
- **Harness vs. model.** Report model and agent harness separately. Hold the model constant where possible.
- **Hermetic.** Each task runs in a container with its own tests.
- **Contamination-aware.** A private held-out split (`tasks/heldout/`, git-ignored) and versioned task sets.

## Layout

```
kilmeh/
├── README.md
├── CLAUDE.md                 # agent instructions (Loom / Claude Code)
├── docs/
│   ├── MARKET_RESEARCH.md    # landscape + gaps
│   └── ROADMAP.md            # milestones and agent work breakdown
├── tasks/                    # task definitions
│   ├── SCHEMA.md             # task format (source of truth)
│   ├── REVIEW_PROCESS.md     # native-speaker review of prompts
│   ├── CHANGELOG.md          # task versions
│   ├── a-prompts/            # 4 tasks
│   ├── b-arabic-in-code/     # 6 tasks
│   └── c-rtl-ui/             # 9 tasks (3 bidi, v1.1)
├── pyproject.toml
├── src/kilmeh/
│   ├── tasks/                # schema models + validator (`kilmeh validate-tasks`)
│   ├── selftest.py           # reference passes, known-bad fails (`kilmeh selftest`)
│   ├── harbor.py             # Harbor export (`kilmeh export-harbor`)
│   └── graders/              # shared RTL checks (Playwright)
├── site/contribute/          # contributor website
├── tests/
└── results/                  # run write-ups
```

Each task is a folder with `task.toml`, prompt variants, a fixture, a Dockerfile, its own grader, a reference solution that passes and a known-bad solution that fails. The format is in [`tasks/SCHEMA.md`](tasks/SCHEMA.md).

## Development

Needs Python 3.12 and [`uv`](https://docs.astral.sh/uv/). Docker is needed only to run a task's grader in its container.

```
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run kilmeh validate-tasks tasks
uv run kilmeh selftest tasks   # needs Docker: reference passes, known-bad fails
uv run kilmeh results-page out.html JOBS_DIR [JOBS_DIR ...]   # static results page, one row per agent
```

### Rerun one task

Needs Docker. Harbor runs the task in a container; the `oracle` agent applies the reference solution, so this costs nothing and should score 1.0.

```
uv run kilmeh export-harbor out tasks/b-arabic-in-code/arabic-file-io
uvx --from harbor==0.25.0 harbor run -p out/arabic-file-io--en -a oracle
```

On Windows, set `PYTHONUTF8=1` first, or Harbor fails to read tasks that hold Arabic text.

Swap `-a oracle` for a real agent (for example `-a codex` with a local Ollama model) to test it. Read the run with `uv run kilmeh summarize-run jobs`.

Contribute words: a static page where native speakers add Arabic and Arabizi spellings lives in [`site/contribute/`](site/contribute/README.md).

## License

- Code: Apache-2.0 (`LICENSE`)
- Task data and results: CC BY 4.0 (`DATA_LICENSE.md`)
