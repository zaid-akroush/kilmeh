# Native-review record: rtl-bidi-name-slots

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

The notification templates below were drafted by an agent and are not reviewed. Each must read as a natural Arabic notification. The board may reword them, but the slot must stay where it is relative to the graded neighbours: in n1 the count `3` follows the name, in n2 Arabic text follows `Notes++`, in n3 Arabic text comes right before `#A-1024`.

| Arabic string | File |
|---|---|
| الإشعارات | index.html (title and heading) |
| أضاف | index.html (n1) |
| منتجات إلى السلة | index.html (n1) |
| تمت إضافة | index.html (n2) |
| إلى المفضلة | index.html (n2) |
| طلبك | index.html (n3) |
| قيد التوصيل | index.html (n3) |
| علقت | index.html (n4) |
| سارة | index.html (n4, Arabic name slot) |
| على منشورك | index.html (n4) |

## Notes and known grader limits

- `bidi_isolated` checks all four slots (computed `unicode-bidi`, any `dir`, or FSI/LRI/RLI ... PDI). `visual_order` checks where the neighbours land on screen: the `3` left of `Ahmad`, `++` right of `Notes`, `#` left of `A`. Isolating without giving Latin values their own direction (`unicode-bidi: isolate` alone, the known-bad) fails n2 and n3.
- `order_n4` checks the verb and the Arabic name in n4 (taken from the pristine text, never retyped) read right to left with their letters in order, so `isolate-override` with `direction: ltr` on the slot fails.
- Known limits of the screen checks (not graded): an overlay with `pointer-events: none` (skipped by `elementFromPoint`) or drawn by a `::before`/`::after` of the graded element itself; paint-only hiding (`color: transparent`, text the same colour as the background, `filter: opacity()`); glyphs overlapping through `letter-spacing`; text changed only on screen by `text-transform` or by `::before`/`::after` `content` (outside textContent); and tokens wrapped onto another line on a narrow layout, which fail even when the order is right.
- `text_kept`: the graded text must equal the fixture's (`tests/pristine_index.html`, a byte copy pinned by `tests/test_rtl_vendoring.py`), ignoring only invisible direction marks (U+2066-2069, U+200E, U+200F), which SPEC.md allows, and all whitespace (reformatting the HTML is fine; reordered words still differ).
- The grader trusts the in-container Chromium and Python, the same tampering limit as the other tracks (see `tasks/SCHEMA.md`).

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
