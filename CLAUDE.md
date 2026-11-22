# Kilmeh: agent instructions

Kilmeh (كلمة, "word") is an open benchmark for coding agents on Arabic prompts, Arabic text in code, and RTL UI. Read `README.md` for scope, `docs/MARKET_RESEARCH.md` for the landscape, `docs/ROADMAP.md` for what to build next.

## Rules

- **Work from `docs/ROADMAP.md`.** Take the first unchecked milestone unless told otherwise. Tick items only when the acceptance criteria are verifiably met.
- **Deterministic grading first.** Prefer tests and DOM/computed-style assertions over LLM or VLM judges. A judge may supplement, never replace.
- **Every task needs a reference solution that passes and a known-bad solution that fails.** No task merges without both.
- **Never machine-translate dialect tasks alone.** Flag them for native-speaker review in the review log. The same goes for Arabizi (Arabic in Latin letters): agents never write final Arabic or Arabizi prompt text. A native speaker writes it; agents insert it byte-for-byte and pin its hash in `tests/`. (v1.0 exception: most Arabic prompts are AI drafts the native speaker approved unchanged; see `docs/DATASET_CARD.md`, Review process.) Process: `tasks/REVIEW_PROCESS.md`.
- **Tasks follow `tasks/SCHEMA.md`** and must pass `uv run kilmeh validate-tasks tasks`. Each task's grader gets its own tests, with one test per check.
- **Preserve Arabic text byte-for-byte.** Don't normalize, transliterate or reorder Arabic in files unless the task requires it. Use UTF-8, no BOM, and keep bidi control characters intact.
- **No secrets in the repo.** API keys come from the environment. `.env*` is git-ignored.
- **Don't commit generated artifacts** (`runs/`, `results/raw/`, `workspaces/`, `tasks/heldout/`). They are in `.gitignore`.
- **Don't edit published task versions in place.** Add a new version and note it in the changelog.
- **Cite sources** for any market or benchmark claim in docs, and mark unverified ones **verify**.

## Open decisions (ask the human, don't guess)

Which agent harnesses are in scope, run budget, domain choice.

Decided: code is Apache-2.0, task data is CC BY 4.0, runner is Python 3.12 with `uv`, Playwright and Docker. Our own task schema is the source of truth and compiles to Harbor task folders later. Arabizi is a prompt field (`script = "latin"`), not a new prompt kind. Current state and decisions: `docs/ROADMAP.md`; maintainers keep sprint notes privately.

## Roles (Loom)

- **CTO**: plans and delegates, doesn't write source.
- **Engineer**: runner, graders, tooling.
- **QA**: grader self-tests, task quality gate, native-review checklist.
- **Reviewer**: checks diffs against these rules.
- **DevOps**: CI, container images, release.

