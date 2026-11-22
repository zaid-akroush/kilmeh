# Native-review record: rtl-bidi-data-cells

Task version: 0.1.0. Process: see `tasks/REVIEW_PROCESS.md`.

`review_status` in `task.toml` is set only by a native speaker, never by an agent. Prompts are short; the full requirements (English, identical for every variant) are in `fixture/SPEC.md`. Fixture Arabic needs native review.

## Variants

| Variant | File | Kind | review_status (task.toml) |
|---|---|---|---|
| en | prompts/en.md | en | draft (AI-written) |
| levantine | prompts/levantine.md | dialect (levantine, Arabic script) | draft (placeholder) |

## Variant: levantine

The file holds only `TODO(board): native Jordanian prompt, see REVIEW.md`. An agent never writes this prompt. The board writes it in Jordanian (Levantine) Arabic with the same requirements as `prompts/en.md`, then sets `review_status`, updates the hash in `tests/test_rtl_vendoring.py` and fills in the section below. `export-harbor` skips the placeholder and `--strict` fails until then.

- Author: (board, native Jordanian speaker)
- Reviewer: none yet
- Date:
- Dialect / spelling notes:
- Meaning matches the English prompt:
- Issues found:

Checklist:

- [ ] Wording is natural for a native speaker, not translationese
- [ ] Same requirements as `prompts/en.md`: nothing added, nothing dropped
- [ ] Identifiers, file names and attribute names (`data-testid`, `dir`) match the fixture exactly
- [ ] File is UTF-8, no BOM, bidi control characters intact

## Fixture content for native review

The table text below was drafted by an agent and is not reviewed. Each string must read as natural Modern Standard Arabic on a settings or system page. In every value cell, Arabic text must come before the value (the `arabic_lead_right` check reads the cell's first text) and must contain no digits.

| Arabic string | File |
|---|---|
| معلومات النظام | index.html (title and heading) |
| البند | index.html (header) |
| القيمة | index.html (header) |
| ملف السجل | index.html (label) |
| يحفظ في | index.html (path cell) |
| الإصدار | index.html (label) |
| الإصدار الحالي | index.html (version cell) |
| الدعم | index.html (label) |
| اتصل على | index.html (phone cell) |
| ملاحظة | index.html (label) |
| استخدم | index.html (code cell) |
| قبل الحفظ | index.html (code cell) |

## Notes and known grader limits

- `visual_order` checks each value's tokens read left to right on screen (`/` before `var`, `2.4.1` before `build`, the four phone groups, `getUser` before `(`). `arabic_lead_right` (task-local) checks the cell's opening Arabic text sits right of the value, with the letters of its first Arabic word in right-to-left order (a bidi-override wrapper fails). `cells_rtl` reads the computed direction of the table, a header cell, the first label cell and the first value cell.
- Switching the whole value column to `direction: ltr` (the known-bad) moves the Arabic to the left, and still reverses the phone groups: after Arabic letters, digits are Arabic numbers to the bidi algorithm.
- Known limits of the screen checks (not graded): an overlay with `pointer-events: none` (skipped by `elementFromPoint`) or drawn by a `::before`/`::after` of the graded element itself; paint-only hiding (`color: transparent`, text the same colour as the background, `filter: opacity()`); glyphs overlapping through `letter-spacing`; text changed only on screen by `text-transform` or by `::before`/`::after` `content` (outside textContent); and tokens wrapped onto another line on a narrow layout, which fail even when the order is right.
- `text_kept`: the graded text must equal the fixture's (`tests/pristine_index.html`, a byte copy pinned by `tests/test_rtl_vendoring.py`), ignoring only invisible direction marks (U+2066-2069, U+200E, U+200F), which SPEC.md allows, and all whitespace (reformatting the HTML is fine; reordered words still differ).
- The grader trusts the in-container Chromium and Python, the same tampering limit as the other tracks (see `tasks/SCHEMA.md`).

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
