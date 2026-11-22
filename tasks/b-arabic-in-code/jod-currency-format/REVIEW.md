# Native-review record: jod-currency-format

**2026-11-21:** the `en` and `levantine` prompts are AI drafts that the board (native Jordanian speaker) approved unchanged in chat. Hashes are pinned in `tests/`. Per the process, the board sets `review_status` itself. Fixture Arabic still needs native review.

Task version: 0.1.0. Process: see `tasks/REVIEW_PROCESS.md`.

`review_status` in `task.toml` is set only by a native speaker, never by an agent. No second native speaker has checked this task yet.

## Variants

| Variant | File | Kind | review_status (task.toml) |
|---|---|---|---|
| en | prompts/en.md | en | draft (AI-written) |
| levantine | prompts/levantine.md | dialect (levantine, Arabic script) | draft (AI draft, board-approved in chat 2026-11-21) |

## Variant: levantine

Filled 2026-11-21: an AI draft that the board (native Jordanian speaker) approved unchanged in chat; hash pinned in `tests/`. `review_status` stays `draft` until the board sets it in the v1.1 review. Not exported or run in v1.0.

- Author: (board, native Jordanian speaker)
- Reviewer: none yet
- Date:
- Dialect / spelling notes:
- Meaning matches the English prompt:
- Issues found:

Checklist:

- [ ] Wording is natural for a native speaker, not translationese
- [ ] Same requirements as `prompts/en.md`: nothing added, nothing dropped
- [ ] Identifiers (`formatJOD`, `receiptText`, `en-JO`, `ar-JO`, `ar-JO-u-nu-arab`, `RangeError`, `Intl`, `BigInt`) match the fixture exactly
- [ ] Code points (U+066B, U+066C, U+0660 to U+0669) are quoted exactly
- [ ] File is UTF-8, no BOM

## Questions for the board

1. **Layout.** Board answers 2026-11-20: symbol `JD` (not CLDR's `U+062F U+002E U+0623 U+002E`), Western digits by default for `ar-JO`. The task therefore expects `1,234.500 JD` for `ar-JO` (number first, one ASCII space, `JD`) and `JD 1,234.500` for `en-JO`. **Please confirm the `1,234.500 JD` layout** (number before the symbol, ASCII space, no bidi marks) is what Jordanian users expect, or give the layout you want.
2. **Arabic-Indic variant.** `ar-JO-u-nu-arab` uses the same layout with U+0660 to U+0669, U+066C and U+066B. Is U+066C the grouping mark Jordanian users expect (versus `,` or U+060C), and is U+066B the decimal mark?
3. **Negatives.** A leading ASCII `-` before everything (`-JD 1,234.500`, `-1,234.500 JD`), no U+061C or U+200F. Acceptable?
4. **Three decimals.** JOD has three decimals (ISO 4217 / CLDR: **verify**; fils are 1/1000 dinar). Confirm it is right to always show three, including `JD 1.000`.

## Fixture content for native review

The fixture, solutions and grader contain no Arabic words: only digits and separators written as `\u` escapes (the files are ASCII). Receipt item names in the grader (`Tea`, `Coffee`, `Falafel`, `Hummus`, `Bread`, `Olives`, `Labneh`) are ASCII English.

| Characters | Code points | Where | Question for the board |
|---|---|---|---|
| Arabic-Indic digits 0 to 9 | `\u0660` to `\u0669` | tests/verify.mjs, solutions/reference | none (standard) |
| Arabic thousands separator | `\u066c` | same | question 2 |
| Arabic decimal separator | `\u066b` | same | question 2 |

## Notes and known grader limits

- **Not CLDR, on purpose.** The pinned image (`node:22.23.5-bookworm-slim`, Node 22.23.5, ICU 78.3, Unicode 17.0) gives, for 1234.5 dinars with `Intl.NumberFormat(locale, {style: "currency", currency: "JOD"})`: `en-JO` `JOD 1,234.500`; `ar-JO` `U+200F U+0661 U+066C U+0662 U+0663 U+0664 U+066B U+0665 U+0660 U+0660 U+0020 U+062F U+002E U+0623 U+002E U+200F` (Arabic-Indic digits, symbol U+062F U+002E U+0623 U+002E, RLM marks); `ar-JO-u-nu-latn` the same with Western digits. The task expects different strings, so the currency-style Intl alternative scores 0 (`tests/b_alternatives/jod-currency-format/intl.js`, docker test in `arabic-in-code.yml`). Expected strings are hard-coded in `tests/verify.mjs`, so the grade cannot change with ICU.
- **Any method is allowed.** Grading is output-only: the prompt says the ICU/CLDR output cannot be used as-is, not that `Intl` is banned. An `Intl` `style: "decimal"` solution that adds `JD` itself scores 1 (`tests/b_alternatives/jod-currency-format/intl_decimal.js`, docker-tested); the currency-style one scores 0.
- Parent/worker grader (`tasks/SCHEMA.md`, "Track B graders"): the agent's code runs only in `tests/worker.mjs`, as uid 65534 in its own session; `tests/verify.mjs` holds the expected values and decides. `test.sh` locks `/tests` before verify, and verify refuses to grade if anything under it is reachable by another user. The worker reads its calls from stdin before agent code loads and writes its result to a file descriptor the parent holds; stdout and stderr are discarded.
- Per-run random inputs: 200 values for `three_decimals_hidden` and 9 receipts are drawn fresh each run and checked against a second hand-written formatter in the grader.
- Remaining limit: grading runs in the solution's own container, so a root `solve.sh` could tamper with `node` before grading (`tasks/SCHEMA.md`, Known limits).

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
