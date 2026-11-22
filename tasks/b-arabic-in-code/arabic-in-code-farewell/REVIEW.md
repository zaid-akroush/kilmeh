# Native-review record: arabic-in-code-farewell

**2026-11-21:** the `en` and `levantine` prompts are AI drafts that the board (native Jordanian speaker) approved unchanged in chat. Hashes are pinned in `tests/`. Per the process, the board sets `review_status` itself. Fixture Arabic still needs native review.

Task version: 0.1.2. Process: see `tasks/REVIEW_PROCESS.md`.

`review_status` in `task.toml` is set only by a native speaker, never by an agent: `native_authored` by a native author who wrote the text, `native_reviewed` by a second native speaker who checked it. Record who and when below.

## Variants

| Variant | File | Kind | review_status (task.toml) |
|---|---|---|---|
| en | prompts/en.md | en | draft |
| levantine | prompts/levantine.md | dialect (levantine, Arabic script) | draft (AI draft, board-approved in chat 2026-11-21) |

Add a section below for every new variant (dialect, code-switched, Arabizi).

## Variant: levantine

Filled 2026-11-21: an AI draft that the board (native Jordanian speaker) approved unchanged in chat; hash pinned in `tests/`. `review_status` stays `draft` until the board sets it in the v1.1 review. Not exported or run in v1.0.

- Author:
- Reviewer:
- Date:
- Dialect / spelling notes:
- Meaning matches the English prompt: yes / no
- Issues found:

Checklist:

- [ ] Wording is natural for a native speaker, not translationese
- [ ] Same requirements as `prompts/en.md`: nothing added, nothing dropped
- [ ] Code identifiers, file names and quoted Arabic strings match the fixture exactly
- [ ] Diacritics and hamza spelling are intentional
- [ ] File is UTF-8, no BOM, bidi control characters intact

## Variant: en

- Author:
- Reviewer:
- Date:
- Meaning check: n/a (reference text)
- Issues found:

## Grader notes

- Parent/worker grader (0.1.1): names drawn at random per run, so a forged worker output cannot pass. Remaining limit: code in the worker could read the names from the worker's own memory and forge the right answers.
- No top-level `def` check (0.1.2): 0.1.1 also required `farewell` to be a top-level `def` in `تحية.py` (ast on the source). The prompt never states that rule, it scored correct solutions 0 (`farewell = _farewell`, or `from _farewell import farewell`), and it stopped nothing beyond the remaining limit above (the in-memory forge plus a one-line stub `def` scored 1 on 0.1.1). It is removed, with its in-memory forge test. The worker now also appends the app directory to the end of `sys.path`, as the other Track B workers do, so `تحية.py` can import a helper module. Pinned by `test_reference_bound_by_assignment_scores_1` and `test_reference_reexported_from_another_module_scores_1` in `tests/test_seed_task_001.py`.

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
