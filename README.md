<p align="center">
  <img src=".github/banner.png" alt="Kilmeh" width="720">
</p>

<h3 align="center">Do AI coding agents work for Arabic users?</h3>

<p align="center">
  Arabic requests · Arabic text in code · right-to-left screens
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

## What is this?

AI coding agents, like Claude Code and Codex, write code when you ask them to. Kilmeh checks whether they do that well **for Arabic users**.

It asks three simple questions:

1. **Do they understand you in Arabic?** We give the agent the same job in English, in Jordanian Arabic, and in Arabizi (Arabic typed with Latin letters and numbers, like `3'ayerha`). Then we compare the results.
2. **Do they keep Arabic text safe?** When an agent edits a file that holds Arabic words, the words must stay exactly the same. No broken letters, no changed spelling.
3. **Can they build Arabic screens?** Arabic reads right to left. We check that pages the agent builds or fixes really work right to left, by opening them in a real browser.

Every answer is checked by code, not by another AI. A task passes or fails, and anyone can rerun it and get the same check.

## Status: v1.0

- **19 tasks**: 4 on Arabic requests, 6 on Arabic text in code, 9 on right-to-left screens.
- **Jordanian only.** The Arabic and Arabizi requests were written or approved by one native Jordanian speaker. Some prompts are still marked `draft`; a full native review comes in v1.1.
- **First results**: Claude Code and Codex, run on a small free model on one laptop. Read them in [`results/v1-run-2026-11.md`](results/v1-run-2026-11.md). These results show the benchmark works. They do not say how the best paid AI models score.
- **Interesting early sign**: requests in Arabizi passed much less often (6 of 24 tries) than the same requests in English (20 of 24). The sample is too small to call it a finding yet.

What comes next is in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## How a task works

Each task is a small project in a folder:

1. A starting project with a problem in it (for example, a page that breaks in Arabic).
2. The request, written in English and in Arabic.
3. A checker that decides pass or fail.
4. A correct solution that must pass, and a wrong one that must fail. This proves the checker works.

Tasks run in [Harbor](https://docs.harborframework.com), a common tool for testing coding agents. The full format is in [`tasks/SCHEMA.md`](tasks/SCHEMA.md).

## Why it matters

Other Arabic AI tests check knowledge or short code snippets. Other coding-agent tests change the programming language, not the human language. Nobody else tests agents on right-to-left screens, Jordanian and Arabizi requests, or keeping Arabic text safe during edits. Sources: [`docs/MARKET_RESEARCH.md`](docs/MARKET_RESEARCH.md).

## Help with words

Native speakers can add how they spell Arabic words in Latin letters at [kilmeh.github.io/contribute](https://kilmeh.github.io/contribute).

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

Needs Python 3.12 and [`uv`](https://docs.astral.sh/uv/). Docker is needed to run tasks and graders in their containers.

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

On Windows, set `PYTHONUTF8=1` first, or Harbor fails to read tasks that hold Arabic text. The full `pytest` suite expects Linux (CI runs it there). On Windows, many tests fail for environment reasons only: `bash` resolving to WSL, symlinks needing admin rights, and CRLF checkouts.

Swap `-a oracle` for a real agent (for example `-a codex` with a local Ollama model) to test it. Read the run with `uv run kilmeh summarize-run jobs`.

Contribute words: a static page where native speakers add Arabic and Arabizi spellings lives in [`site/contribute/`](site/contribute/README.md).

## License

- Code: Apache-2.0 (`LICENSE`)
- Task data and results: CC BY 4.0 (`DATA_LICENSE.md`)
