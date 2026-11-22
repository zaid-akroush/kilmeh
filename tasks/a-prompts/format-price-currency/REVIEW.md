# Native-review record: format-price-currency

Task version: 0.1.0. Process: see `tasks/REVIEW_PROCESS.md`.

`review_status` in `task.toml` is set only by a native speaker, never by an agent. The `levantine` and `arabizi_levantine` prompts were drafted by an agent (style modelled on public Jordanian developer posts, nothing copied) and approved unchanged by the board, a native Jordanian speaker, on 2026-11-21. Their hashes are pinned in `tests/test_a_skeletons.py`. The English prompt is still an AI draft.

## Variants

| Variant | File | Kind | review_status (task.toml) |
|---|---|---|---|
| en | prompts/en.md | en | draft (AI-written) |
| arabizi_levantine | prompts/arabizi_levantine.md | dialect (levantine, latin script) | native_reviewed (AI draft, board-approved 2026-11-21) |
| levantine | prompts/levantine.md | dialect (levantine, Arabic script) | native_reviewed (AI draft, board-approved 2026-11-21) |

## Variant: levantine

Filled 2026-11-21: an AI draft that the board (native Jordanian speaker) approved unchanged; hash pinned in `tests/`. Not yet checked by a second native speaker.

- Author: (board, native Jordanian speaker)
- Reviewer: none yet
- Date:
- Dialect / spelling notes:
- Meaning matches the English prompt:
- Issues found:

Checklist:

- [ ] Wording is natural for a native speaker, not translationese
- [ ] Same requirements as `prompts/en.md`: nothing added, nothing dropped
- [ ] Code identifiers and file names match the fixture exactly
- [ ] Diacritics and hamza spelling are intentional
- [ ] File is UTF-8, no BOM, bidi control characters intact

## Variant: arabizi_levantine

Filled 2026-11-21: an AI draft that the board (native Jordanian speaker) approved unchanged; hash pinned in `tests/`. Not yet checked by a second native speaker.

- Author: (board, native Jordanian speaker)
- Reviewer: none yet
- Date:
- Dialect / spelling notes:
- Meaning matches the English prompt:
- Issues found:

Checklist:

- [ ] Wording is natural for a native speaker, not translationese
- [ ] Same requirements as `prompts/en.md`: nothing added, nothing dropped
- [ ] Code identifiers and file names match the fixture exactly
- [ ] File is UTF-8, no BOM

## Variant: en

AI draft in plain everyday wording. Reviewer: none yet.

## Fixture content for native review

None: the fixture has no Arabic.

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
