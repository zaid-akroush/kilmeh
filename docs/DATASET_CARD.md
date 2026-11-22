---
# Hugging Face dataset card metadata. Format: https://huggingface.co/docs/hub/datasets-cards
license: cc-by-4.0
language:
  - ar
  - en
pretty_name: Kilmeh
task_categories:
  - text-generation
tags:
  - benchmark
  - coding-agents
  - code
  - arabic
  - levantine
  - arabizi
  - rtl
size_categories:
  - n<1K
---

# Dataset card: Kilmeh

Filled from the repo on 2026-11-22 (19 tasks on `main`). Update the counts whenever tasks are added.

## Summary

Kilmeh ("word" in Arabic) is an open benchmark for coding agents such as Claude Code and Codex on Arabic prompts, Arabic text inside code, and right-to-left (RTL) user interfaces. Each item is a task: a starting repo, prompt variants in English and Arabic, a container, a deterministic grader, a reference solution that passes and a known-bad solution that fails.

Status: v1.0. First results on a small local model: [`results/v1-run-2026-11.md`](../results/v1-run-2026-11.md). See [`ROADMAP.md`](ROADMAP.md).

- Repository: https://github.com/kilmeh/kilmeh
- Version: `v1.0.0` (per-task versions are in [`tasks/CHANGELOG.md`](../tasks/CHANGELOG.md))
- Leaderboard: none. Results pages for each run are in [`results/`](../results/).

## Tracks

Counts read from `tasks/` on 2026-11-22.

| Track | Question | Tasks now | Long-term target |
|---|---|---|---|
| `a-prompts` | Does task success hold when the instruction is Arabic (MSA, dialect, code-switched, Arabizi) instead of English? | 4 | 15 |
| `b-arabic-in-code` | Are Arabic comments, strings, identifiers and file contents kept byte-for-byte through edits? | 6 | 10 |
| `c-rtl-ui` | Does generated or edited UI work right-to-left? | 9 (3 bidi, v1.1) | 15 |
| `d-output-language` | Does the agent answer, comment and write commits in the requested language? | 0 | planned |
| **Total** | | **19** | 40 |

Grader types in use: read them from `tasks/*/*/task.toml`. `language-id` is in the schema but no task uses it yet.

## Languages and variants

Each task has at least one English prompt and at least one Arabic-script prompt (`lang = "ar"`, `script = "arabic"`). Prompt kinds (`kind`): `en`, `msa` (Modern Standard Arabic), `dialect`, `code-switched`.

- **Dialects:** the schema allows `levantine`, `gulf`, `egyptian`, `maghrebi`, `iraqi`, `sudanese`, `other`. Every dialect prompt today is `levantine` (Jordanian).
- **Arabizi** (Arabic typed in Latin letters and digits) is not a separate kind. It is a dialect prompt with `script = "latin"`. A task may carry several Arabizi spellings under one `pair_id`. Arabizi has no standard spelling. Kilmeh keeps the native author's natural typing on purpose (board, 2026-11-22), for example `3'` for غ and `6` for ط, because that is how real users type. Kilmeh does not clean it to one house style. A spelling that changes results is a finding, not noise to remove.
- **Current prompt state (2026-11-22):** Track A has 4 tasks, each with English, Jordanian and Jordanian Arabizi prompts written or approved by the board. Tracks B and C have short English and Jordanian prompts, with full requirements in each task's `fixture/SPEC.md`. The board is reviewing every prompt in chat; prompts still marked `draft` are not exported. No MSA prompts ship in v1.0.

## Data fields

One folder per task, `tasks/<track>/<task-id>/`. Full rules: [`tasks/SCHEMA.md`](../tasks/SCHEMA.md).

| Field (`task.toml`) | Meaning |
|---|---|
| `schema_version` | `"1"` |
| `id` | kebab-case, equals the folder name |
| `version` | semver of the task |
| `track` | one of the four tracks above |
| `title` | short English title |
| `difficulty` | `easy`, `medium`, `hard` |
| `split` | `public` or `heldout` |
| `pair_id` | optional; groups prompt variants of one underlying task |
| `stack` | optional list, e.g. `["python"]`, `["react", "esbuild", "css"]` |
| `[prompts.<variant>]` | `file`, `lang` (`en`/`ar`), `kind`, `script` (`arabic`/`latin`), `dialect` (only for `kind = "dialect"`), `review_status` (`draft`/`native_authored`/`native_reviewed`) |
| `[grader]` | `type`, `entry` (a file in `tests/`), `timeout_seconds` |
| `[solutions]` | `reference` and `known_bad` folders |

Files: `prompts/<variant>.md` (UTF-8, no BOM, bytes kept exactly as written), `fixture/` (starting repo), `environment/Dockerfile`, `tests/` (grader), `solutions/reference/` and `solutions/known-bad/` (each with `solve.sh`), `REVIEW.md` (native review log).

The grader writes `1` (pass) or `0` (fail). Run contract: [`tasks/SCHEMA.md`](../tasks/SCHEMA.md#run-contract).

Not on Hugging Face yet. When it is, the layout follows `kilmeh export-harbor`: one row per task and prompt variant.

## How tasks are made

- **Native speakers write the Arabic.** Final Arabic and Arabizi prompt text is written by a native speaker. Agents never write it; they insert it byte-for-byte and pin its hash in `tests/`. Dialect and Arabizi prompts are never machine-translated.
- **Reference and known-bad.** Every task ships a reference solution that must pass and a known-bad solution that must fail. `uv run kilmeh selftest` proves reference = 1, known-bad = 0 and untouched fixture = 0, and CI runs it on every change.
- **Deterministic graders.** Pass or fail comes from tests, byte checks, and DOM or computed-style checks in headless Chromium. No LLM or VLM judge decides a score. Each grader check has its own test.
- **Hermetic.** Each task runs in its own container. The self-test and the RTL graders run with no network access, while agent runs need network to reach the model.

## Review process

Every prompt variant carries a `review_status`. A variant starts as `draft`, becomes `native_authored` when a native speaker wrote it, and `native_reviewed` after a second native speaker checks it. Each change is logged in the task's `REVIEW.md`. Releases require `uv run kilmeh validate-tasks --strict tasks`, which rejects every draft. Details: [`tasks/REVIEW_PROCESS.md`](../tasks/REVIEW_PROCESS.md).

## Licensing

- Task data (task definitions, prompts, fixtures, results under `tasks/` and `results/`): CC BY 4.0. See [`DATA_LICENSE.md`](../DATA_LICENSE.md).
- Code (runner, graders, tooling): Apache-2.0. See [`LICENSE`](../LICENSE).
- Held-out tasks are not published and not covered by the data licence.

## Limitations and biases

- **Dialect coverage:** only Jordanian (Levantine) so far. Gulf, Egyptian, Maghrebi, Iraqi and Sudanese are not covered. Results do not speak for Arabic speakers as a whole.
- **One native reviewer:** all native-authored text comes from one Jordanian speaker. A second annotator is future work.
- **Small size:** 19 tasks, and only the 4 Track A tasks have a Jordanian and Arabizi pair for the English prompt. With 1 try per variant, one trial moves a pass rate by up to 100 points, so v1.0 makes no claim that dialect or Arabizi lowers agent success. Each results write-up fixes what it may claim before results are read.
- **Local small-model results are not representative:** v1.0 runs use a small local model (Qwen 3.5 9B on Ollama, through Claude Code and Codex CLI) at half the normal agent time. Those scores say nothing about frontier agents.
- **Grader limits:** grading runs in the solution's own container, so a solution with root could tamper with grader tools. Other accepted limits are listed in [`tasks/SCHEMA.md`](../tasks/SCHEMA.md#known-limits).
- **Arabizi language ID:** off-the-shelf language-ID tools tend to label Arabizi as English (**verify**), so Track D will need a custom check.
- **Measured in v1.0** (`results/v1-run-2026-11.md`): Arabizi prompts passed 6 of 24 Track A trials against 20 of 24 for English, on 4 tasks. Not significant, but it means Arabizi results are the least stable part of the set. Timeouts were frequent at half agent time (Codex lost 18 of 30 trials), so slow agents score lower than their skill.

## Contamination

- A private held-out split lives only in `tasks/heldout/`. It is git-ignored and never committed or uploaded. The validator rejects `split = "heldout"` outside that folder, and `kilmeh export-harbor` refuses held-out tasks.
- Public tasks will appear on the web and may end up in training data. Task sets are versioned so results can name the set they used.
- Not yet: a canary string, and a policy for rotating held-out tasks into the public set. Planned before the held-out split is used.

## Citation

```bibtex
@misc{kilmeh,
  title  = {Kilmeh: a benchmark for coding agents on Arabic},
  author = {Akroush, Zaid},
  year   = {2026},
  url    = {https://github.com/kilmeh/kilmeh}
}
```

## Contact

Open an issue at https://github.com/kilmeh/kilmeh/issues.
