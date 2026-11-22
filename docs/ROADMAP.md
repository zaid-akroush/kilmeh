# Kilmeh Roadmap

Written so agents (under Loom) can pick up a milestone and run. Each milestone has acceptance criteria that QA/reviewer agents can check. Items marked **(board)** are ticked by the maintainer only: they need a decision or native Arabic an agent cannot produce.

Take the first unchecked item in the first open milestone.

## Done: foundations (M0 to M3)

- [x] Licences: Apache-2.0 code (`LICENSE`), CC BY 4.0 data (`DATA_LICENSE.md`).
- [x] Name reserved: GitHub org `kilmeh`, PyPI placeholder `kilmeh` 0.0.1. No domain yet.
- [x] Tooling: Python 3.12 with `uv`, Playwright for UI graders, Docker for task sandboxes. CI runs ruff, pytest and the task self-test on every PR.
- [x] Task schema `tasks/SCHEMA.md` and validator `kilmeh validate-tasks` (PR #3). Arabizi is a prompt field (`script = "latin"`). Dataset card: `docs/DATASET_CARD.md`.
- [x] Runner: Harbor (`harbor==0.25.0`), decided 2026-11-20. Kilmeh exports tasks (`kilmeh export-harbor`) and reads run folders (`kilmeh summarize-run`, `--jsonl` in PR #64, format in `docs/RESULTS_FORMAT.md`). No own runner or agent adapters.
- [x] Graders: test-based (`kilmeh selftest`), Arabic text integrity (PR #62), RTL in Playwright (PRs #28 to #32), language ID (PR #63, Arabizi not detected).
- [x] Every task has a reference solution that passes and a known-bad solution that fails; CI proves it on every change.

## v1.0: Jordanian, small, basics right

Decided 2026-11-21: one dialect, Jordanian (`levantine`, plus Jordanian Arabizi). No MSA, no other dialects, no 40-task target. Runs use local models only; no paid runs.

- [x] Track A: 4 tasks, each with `en`, `levantine` and `arabizi_levantine` prompts written or approved by the native maintainer, hashes pinned (PR #70).
- [x] Track B: 6 tasks, short prompts plus `fixture/SPEC.md` (PR #72).
- [x] Track C: 6 tasks with a Jordanian prompt, requirements in `fixture/SPEC.md` (PR #71).
- [x] README rerun guide checked from a clean clone (2026-11-21).
- [x] Failure causes in `summarize-run`: setup timeout, agent timeout, harness error, tests failed (PR #77). Wilson 95% intervals and a paired McNemar table (PR #81).
- [x] Static results page: `kilmeh results-page` (PR #87).
- [x] Local-model run: Claude Code and Codex CLI on Qwen 3.5 9B through Ollama, 1 try per variant, plus 2 more tries on Track A (PR #89).
- [x] Parity table: English vs Jordanian vs Arabizi for every Track A task, 3 tries (PR #89).
- [x] Write-up with real failure examples, which fixed what it may claim before results were read: `results/v1-run-2026-11.md` (PR #89).
- [x] Second local model checked (Ornith 9B); no clear difference, Qwen stays the reference (PR #89).
- [ ] Clean public repository `zaid-akroush/kilmeh` holds the v1.0 snapshot.
- [ ] **(board)** Repository public, tag `v1.0.0`.
- **Done when:** a stranger can clone the public repo, rerun one task, and read the write-up.

## v1.1: native review and mixed-direction text

- [x] Three mixed Arabic/English text (bidi) tasks in Track C, English prompts, `visual_order` and `text_kept` checks (PR #86).
- [ ] **(board)** Jordanian prompts for the three bidi tasks.
- [ ] **(board)** Native review of every remaining prompt (6 of 21 decided, resumes at `arabic-in-code-farewell`). An engineer applies the decisions: new task versions where text changed, `review_status`, `REVIEW.md`, changelog.
- [ ] All tasks pass `validate-tasks --strict` and `selftest` in CI. `--strict` waits on the native review (agents may not set `review_status`, `tasks/REVIEW_PROCESS.md`).
- [ ] **(board)** Jordanian Arabizi prompts for Tracks B and C, so parity covers 16 tasks instead of 4.
- [ ] A bigger Track A run to test the Arabizi gap seen in v1.0 (6/24 vs 20/24 English, not significant at N = 4). Fix what it may claim before it runs.
- [ ] One run at full agent time (no 0.5 timeout multiplier).

## Later

- One frontier-model result, if credits or a budget appear.
- Track D (reply language): tasks that use the `language-id` grader.
- Grow to 40 tasks (15 Track A, 10 Track B, 15 Track C), if native writers can be paid.
- Arabizi spelling dataset from the contributor website, by dialect, under CC BY 4.0.
- Dialect expansion (Gulf first, then Egyptian, Maghrebi, Iraqi, Sudanese), more frameworks (Flutter, React Native, Vue).
- Publish tasks on the Harbor hub and Hugging Face; a held-out submission service.
- Paper (after a literature check confirms the novelty claim in `docs/MARKET_RESEARCH.md`).
