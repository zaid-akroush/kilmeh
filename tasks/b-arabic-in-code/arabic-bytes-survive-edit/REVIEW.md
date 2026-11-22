# Native-review record: arabic-bytes-survive-edit

**2026-11-21:** the `en` and `levantine` prompts are AI drafts that the board (native Jordanian speaker) approved unchanged in chat. Hashes are pinned in `tests/`. Per the process, the board sets `review_status` itself. Fixture Arabic still needs native review.

Task version: 0.1.0. Process: see `tasks/REVIEW_PROCESS.md`.

`review_status` in `task.toml` is set only by a native speaker, never by an agent. No second native speaker has checked this task yet. Both prompts are drafts.

## Variants

| Variant | File | Kind | review_status (task.toml) |
|---|---|---|---|
| en | prompts/en.md | en | draft (AI-written; it quotes two agent-drafted Arabic strings as data, see below) |
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
- [ ] File names and identifiers (`src/strings.ts`, `locale/ar.csv`, `README.md`, `VERSION`, `checkout_title`, `checkout_subtitle`) match the fixture exactly
- [ ] The two quoted lines (the `checkout_subtitle` entry and the CSV row) are copied byte-for-byte from `prompts/en.md` (or replaced together with `ENTRY` and `ROW` in `tests/verify.py`, the reference and the known-bad solution, the alternatives and the pins in `tests/test_b_bytes.py`, as a new task version)
- [ ] Code points (U+200E, U+200F, U+061C, U+202A to U+202E, U+2066 to U+2069, U+200C, U+200D, U+00A0, U+0653, U+FDF2) are quoted exactly
- [ ] File is UTF-8, no BOM
- [ ] States the same rules `prompts/en.md` states: LF with no final newline in `strings.ts`, CRLF in the CSV, no normalization, no BOM, `README.md` unchanged

## Fixture content for native review

All of this was drafted by an agent and needs a native speaker. The fixture is built by `tests/b_fixture_gen/arabic-bytes-survive-edit.py` (every invisible character is an escape there); `tests/golden/` holds the same bytes for the grader. The Arabic is deliberately simple: the task grades bytes, not meaning.

| Content | Where | Question for the board |
|---|---|---|
| `مرحبا بكم في متجرنا` (welcome) | strings.ts, ar.csv | Natural storefront greeting? |
| `الهاتف: ` before a phone number, with U+200F (RLM) before `+962 6 555 0100` and U+200E (LRM) after it | strings.ts `phone` | Is this a realistic use of RLM/LRM around a phone number? |
| `نص عربي` inside U+202B (RLE) ... U+202C (PDF), then `English text` inside U+202A (LRE) ... U+202C | strings.ts `embed` | none (test data) |
| `abc` in U+2066 (LRI) ... U+2069 (PDI), `نص` in U+2067 (RLI) ... U+2069, `مرحبا hello` in U+2068 (FSI) ... U+2069 | strings.ts `isolates` | none (test data) |
| `رقم ` then U+061C (ALM) then `+٩٦٢` (Arabic-Indic digits) | strings.ts `alm` | Is ALM before a plus sign realistic? |
| `كتاب` + U+200C (ZWNJ) + `ها` | strings.ts `zwnj` | Is ZWNJ in `كتابها` ("its book") plausible, or would the board prefer a Persian-style example? |
| `ه` U+200D `ه` U+200D `ه` | strings.ts `zwj_word` | Is this a fair ZWJ shaping example (three haa joined)? |
| 👨‍👩‍👧 (U+1F468 U+200D U+1F469 U+200D U+1F467) | strings.ts `family` | none (emoji ZWJ sequence) |
| `ب` + U+0651 (shadda) + U+064E (fatha) + `ب`: marks in non-canonical order on purpose (NFC reorders them to fatha, shadda) | strings.ts `marks` | Real texts usually write shadda first, then the vowel; confirm that this order is the common one |
| `ا` + U+0653 (maddah) + `خر`: the decomposed form of `آخر`, kept decomposed on purpose (NFC composes it) | strings.ts `nfd` | none (test data) |
| U+FDF2 (the Allah ligature) alone | strings.ts `allah` | none (test data) |
| `10` + U+00A0 (NBSP) + `JD` | strings.ts `nbsp` | none |
| `إتمام الشراء` (checkout title), `سلتك فارغة` (your cart is empty), `قيمة` (value, on the line with trailing spaces) | strings.ts, ar.csv | Natural UI wording? |
| **Quoted in the prompt and graded:** `راجع طلبك قبل الدفع` ("review your order before paying") as the new `checkout_subtitle` value, in both the TypeScript entry and the CSV row | prompts/en.md, tests/verify.py, solutions, tests | Natural subtitle? A change needs a new task version, not an edit |

Invisible characters in the table are listed by code point so they survive a copy and paste.

## Notes and known grader limits

- The grader never runs agent code. It reads the bytes of `src/strings.ts`, `locale/ar.csv` and `README.md` once, then compares them with `tests/golden/` (not in the image at agent time; `test_dockerfile_copies_only_the_fixture_and_pins_the_image`). Expected values come from the golden bytes plus the three requested edits.
- Feature lines are found by their key (`  phone:`, `  marks:` and so on) and compared per feature (bidi controls by code point and offset, joiners by code point and offset, the whole line for marks, NFD and NFKC-sensitive lines). `untouched_lines_identical` is a byte-line `SequenceMatcher` (no autojunk) over both edited files; only the version replace, the entry insert after `checkout_title` and the CSV row insert at the end are allowed. So each preservation check fails together with `untouched_lines_identical`, and the sets are pinned exactly in `tests/test_b_bytes.py`.
- A symlinked file or directory in `/app`, a non-regular file, or a file over 1 MB scores 0 on every check. `verify.py` refuses to grade (exit 2) unless `/tests` is root-owned with no group or other access, kills uid 65534 processes before and after reading `/app`, and runs with `-B -I -S` and `dont_write_bytecode`.
- No random inputs: the edit is fixed and the whole input is the files themselves, so there is nothing to draw per run. Hard-coding is possible but harmless: `tests/golden/` holds the same bytes as `fixture/` (`test_generator_reproduces_fixture_and_golden_bytes`), so a solution that writes out the three edited files verbatim has simply done the task. What the grader guarantees is narrower: the three files, read once, must equal the golden bytes plus exactly the three requested edits. It does not check how the files were produced.
- A daemon that runs as root and rewrites `/app` after the snapshot has no effect (the snapshot is read once), but one that rewrites it before the snapshot is part of the solution. A root `solve.sh` that tampers with `python3` before grading is the usual known limit (`tasks/SCHEMA.md`).
- Trailing spaces, the first comment line and the blank line are graded only through `untouched_lines_identical`.

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
