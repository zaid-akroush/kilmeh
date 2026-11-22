# Native-review record: rtl-order-summary-fix

Task version: 0.1.0. Process: see `tasks/REVIEW_PROCESS.md`.

`review_status` in `task.toml` is set only by a native speaker, never by an agent. The `levantine` prompt was drafted by an agent (style modelled on public Jordanian developer posts, nothing copied) and approved unchanged by the board, a native Jordanian speaker, on 2026-11-21. Its hash is pinned in `tests/test_rtl_vendoring.py`. Prompts are short; the full requirements (English, identical for every variant) are in `fixture/SPEC.md`. Fixture Arabic still needs native review.

## Variants

| Variant | File | Kind | review_status (task.toml) |
|---|---|---|---|
| en | prompts/en.md | en | draft (AI-written) |
| levantine | prompts/levantine.md | dialect (levantine, Arabic script) | native_reviewed (AI draft, board-approved 2026-11-21) |

## Variant: levantine

Filled 2026-11-21: an AI draft that the board (native Jordanian speaker) approved unchanged; hash pinned in `tests/`. Not yet checked by a second native speaker.

- Requirement to carry over: the order summary table itself must fit a 360 px screen with no horizontal scrolling of the table or the page, and must not be shrunk with `transform` or `zoom` (the `table_fits` check is strict; `prompts/en.md` says so).
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

The page text below was drafted by an agent and is not reviewed. Each string must read as natural Modern Standard Arabic (or Jordanian where it fits) in a real page. A string the board changes must be changed in the fixture (and in the reference solution if it appears there) in the same pull request.

| Arabic string | File |
|---|---|
| ملخص الطلب | index.html |
| تم استلام طلبك رقم | index.html |
| سنتواصل معك على الرقم | index.html |
| تم إنشاء الطلب بواسطة الحساب | index.html |
| المبلغ الإجمالي المطلوب هو | index.html |
| المنتج | index.html |
| الكمية | index.html |
| السعر | index.html |
| قهوة عربية | index.html |
| كتاب | index.html |
| شاهد الفيديو | index.html |
| الاسم | index.html |
| سارة أحمد | index.html |
| البريد الإلكتروني | index.html |
| رقم الهاتف | index.html |
| السابق | index.html |
| التالي | index.html |

## Notes and known grader limits

- `tests/name_sample.txt` is the Arabic name typed into the name field. It is copied from the fixture's `placeholder` byte for byte (17 bytes, sha256 pinned in `tests/test_rtl_vendoring.py`), never retyped.
- The phone field is `type="text" inputmode="tel"`, because Chromium already renders `type="tel"` left to right and the check could not fail.
- The logo and play icons are drawn with the arrow-like part (`data-part=head`) on the right; the grader expects that side to stay on the right in RTL.
- Known limits (tickets, not fixed): physical CSS inside a closed shadow root is invisible to the CSS checks; `dir` and `lang` set by JavaScript at load time are accepted, because the checks read the DOM after load.
- `svg_markup_unchanged` pins the four icon SVGs to the fixture's markup (digests in `tests/verify.py`), so the arrows must be flipped with CSS as the prompt says. If the fixture's SVG markup is edited, regenerate the digests in the same change.
- The grader trusts the in-container Chromium and Python, the same tampering limit as the other tracks (see `tasks/SCHEMA.md`).

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
