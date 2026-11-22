# Native-review record: rtl-bidi-chat-feed

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

The page text below was drafted by an agent and is not reviewed. Each string must read as natural Arabic in a real comment feed (short user messages, Jordanian where it fits). A string the board changes must be changed in the fixture and in any test script that uses it in the same pull request. The Latin and number tokens the grader looks for (`Ahmad`, `5`, `Hello`, `Thanks`, `https`, `3`, `Sara`, `Omar`, `0791234567`, `Ali`) must stay, in the same order, and each message must keep its first strong letter (Arabic for m1, m4, m5; Latin for m2, m3).

| Arabic string | File |
|---|---|
| التعليقات | index.html (title and heading) |
| ليلى | index.html (author, m1) |
| وصل الطلب مع | index.html (m1) |
| وصل, الطلب, جاهز, الرابط, يعمل, طلبت, من, اتصل, على (word pairs) | tests/arabic_words.json (copied from index.html) |
| الساعة | index.html (m1), tests/rtl_gaming/rtl-bidi-chat-feed/reversed_text.py |
| الطلب جاهز؟ | index.html (m2) |
| عمر | index.html (author, m3) |
| الرابط لا يعمل منذ | index.html (m3) |
| أيام | index.html (m3) |
| ريم | index.html (author, m4) |
| طلبت من | index.html (m4) |
| و | index.html (m4) |
| خالد | index.html (author, m5) |
| اتصل على | index.html (m5) |
| أو | index.html (m5) |

## Notes and known grader limits

- Each message is graded by screen position: `visual_order` finds known Latin and number tokens in the message text, in typed order, and checks they read right to left (Arabic-first message) or left to right (English- or link-first message). Two words of one Arabic run per message (`tests/arabic_words.json`, copied from the fixture's bytes by script, never retyped; pinned by `tests/test_rtl_vendoring.py`) must read right to left as well. A token fails if it is hidden (`visibility`, `display`), fully transparent (`opacity: 0`), covered by another element, mirrored or flipped (`transform`, `scale`, `rotate`), wrapped onto another line, or has its own letters reversed (bidi-override).
- A fixed `dir` per message is accepted (`tests/rtl_alternatives/rtl-bidi-chat-feed/explicit_dir.py`): the page shows correctly. The grader does not check that the solution would work for new messages.
- Known limits of the screen checks (not graded): an overlay with `pointer-events: none` (skipped by `elementFromPoint`) or drawn by a `::before`/`::after` of the graded element itself; paint-only hiding (`color: transparent`, text the same colour as the background, `filter: opacity()`); glyphs overlapping through `letter-spacing`; text changed only on screen by `text-transform` or by `::before`/`::after` `content` (outside textContent); and tokens wrapped onto another line on a narrow layout, which fail even when the order is right.
- `text_kept`: the graded text must equal the fixture's (`tests/pristine_index.html`, a byte copy pinned by `tests/test_rtl_vendoring.py`), ignoring only invisible direction marks (U+2066-2069, U+200E, U+200F), which SPEC.md allows, and all whitespace (reformatting the HTML is fine; reordered words still differ).
- The grader trusts the in-container Chromium and Python, the same tampering limit as the other tracks (see `tasks/SCHEMA.md`).

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
