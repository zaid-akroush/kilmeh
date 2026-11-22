# Native-review record: arabic-digits-parse-format

**2026-11-21:** the `en` and `levantine` prompts are AI drafts that the board (native Jordanian speaker) approved unchanged in chat. Hashes are pinned in `tests/`. Per the process, the board sets `review_status` itself. Fixture Arabic still needs native review.

Task version: 0.1.1. Process: see `tasks/REVIEW_PROCESS.md`.

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
- [ ] Identifiers (`parse_number`, `format_number`, `latn`, `arab`, `arabext`, `ValueError`) match the fixture exactly
- [ ] Code points (U+066B, U+066C, U+0660 to U+0669, U+06F0 to U+06F9) are quoted exactly
- [ ] File is UTF-8, no BOM
- [ ] States the same rules `prompts/en.md` states: return an exact `str` (not a subclass), never write `/app` or read the grader, no file writes at import, exact `Decimal` results

## Fixture content for native review

The fixture, solutions and grader contain no Arabic words: only digits and number separators, all written as `\u` escapes in the source (the files are ASCII). The board should confirm the separator conventions below are what Jordanian users expect.

| Characters | Code points | Where | Question for the board |
|---|---|---|---|
| Arabic-Indic digits 0 to 9 | `\u0660` to `\u0669` | fixture/test_numerals.py, tests/verify.py, solutions | none (standard) |
| Extended Arabic-Indic digits 0 to 9 | `\u06f0` to `\u06f9` | fixture/test_numerals.py, tests/verify.py, solutions | Mostly Persian/Urdu use; keep it in a Jordanian task? |
| Arabic thousands separator | `\u066c` | same | Is U+066C the grouping mark Jordanian users expect with Arabic-Indic digits (versus `,` or U+060C)? |
| Arabic decimal separator | `\u066b` | same | Is U+066B right, and is accepting `.` with Eastern digits on input correct? |
| Visible example inputs | `\u0661\u0662\u0663`, `\u06f1\u066c\u06f2\u06f3\u06f4\u066b\u06f5`, `1\u0662\u0663` | fixture/test_numerals.py | none |
| Visible example output | `\u0661\u066c\u0662\u0663\u0664\u066b\u0665\u0660` | fixture/test_numerals.py | none |

## Notes and known grader limits

- The output never carries U+061C ARABIC LETTER MARK before the minus sign, although CLDR adds it for `arab` (**verify** against CLDR). This is a deliberate, stated choice in the prompt.
- Parent/worker grader (see `tasks/SCHEMA.md`, "Track B graders"): the agent's code runs only in `tests/worker.py`, as uid 65534 in its own session; `tests/verify.py` holds the expected values and decides.
- `test.sh` locks `/tests` (`chown -R 0:0`, `chmod -R go-rwx`) before verify runs, so the worker (uid 65534) cannot read the hidden answers; verify refuses to grade if anything under its `tests/` is still reachable by another user (fail closed). QA's cheat that reads `/tests/verify.py` at import scored 1 before this lock and scores 0 now (`tests/b_gaming/arabic-digits-parse-format/read_tests_cheat.py`).
- Random inputs (0.1.1): the input templates in `tests/verify.py` are public once the grader is, so each run redraws their digits 1-4 and 6-8 (SystemRandom; 0, 5 and 9 stay, keeping zeros, ties and carries) and draws fresh roundtrip values, and verify computes the expected values itself. A module that writes a recorded or precomputed result JSON to the worker's channel and exits now scores 0 (`tests/b_gaming/arabic-digits-parse-format/constant_forge.py` scored 1 on 0.1.0). `test.sh` runs `chmod -R a+rX /app` so a root-only (0600) solution is still readable by the worker. Remaining limit: code in the worker could read the inputs from the worker's memory.
- Remaining limit: grading runs in the solution's own container, so a root `solve.sh` could tamper with `python3` or the stdlib before grading (see `tasks/SCHEMA.md`, Known limits).
- Per-check isolation probes (`tests/b_mutations/arabic-digits-parse-format/`) key on input features that only one check uses: surrounding spaces (`parse_*`), `.` with Eastern digits (`parse_decimal_sep`), five or more grouping separators (`parse_grouping`), positive values at 3 places (`format_*`), exact ties (`format_negative_and_rounding`), magnitudes of 10^10 or more (`roundtrip_seeded`).

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
