# Native-review record: rtl-tailwind-logical-convert

Task version: 0.1.0. Process: see `tasks/REVIEW_PROCESS.md`. Design: `docs/superpowers/specs/2026-11-14-rtl-tailwind-logical-convert-design.md`.

`review_status` in `task.toml` is set only by a native speaker, never by an agent. The `levantine` prompt was drafted by an agent (style modelled on public Jordanian developer posts, nothing copied) and approved unchanged by the board, a native Jordanian speaker, on 2026-11-21. Its hash is pinned in `tests/test_rtl_vendoring.py`. Prompts are short; the full requirements (English, identical for every variant) are in `fixture/SPEC.md`. Fixture Arabic still needs native review.

## Variants

| Variant | File | Kind | review_status (task.toml) |
|---|---|---|---|
| en | prompts/en.md | en | draft (AI-written) |
| levantine | prompts/levantine.md | dialect (levantine, Arabic script) | native_reviewed (AI draft, board-approved 2026-11-21) |

## Variant: levantine

Filled 2026-11-21: an AI draft that the board (native Jordanian speaker) approved unchanged; hash pinned in `tests/`. Not yet checked by a second native speaker.

- Requirements to carry over (all are graded, on each of the three pages): an Arabic `lang` (`ar` or `ar-JO`) and right-to-left on `<html>`; change only `class` attributes and `src/input.css`, without adding, removing, reordering or re-tagging elements; the layout follows `<html dir>` alone and mirrors exactly when only that attribute changes (every element's box mirrors and its padding, borders, corner radii, scroll padding and text alignment swap sides; the left-to-right islands only mirror their position); with `dir="ltr"` every element keeps its original position and size (within 2 px) and its padding, borders, corner radii, scroll padding and text alignment on each side, nothing hidden, clipped, shrunk, scaled or moved; Tailwind logical utilities only, with no physical utility even behind `md:`, `hover:`, `rtl:` or `ltr:`, and no physical CSS property anywhere in the compiled CSS (`@apply`, arbitrary values, hand-written rules and `@import`ed styles included); the elements that carry `dir="ltr"` (email, webhook URL, IBAN, card number) stay left-to-right with their text starting at their left edge; no sideways scrolling at 360 px; all styling from Tailwind classes and `src/input.css`, each page linking only `dist/app.css` (no `<style>`, no `style` attribute, no other stylesheet, no `<script>` even one that removes itself, no `on*` handler), and `dist/` is rebuilt by the grader so editing it has no effect; no leftover file in the project that mentions physical class names (Tailwind scans every file and would compile them); every `data-testid` element kept, visible, with its text unchanged.
- Author: (board, native Jordanian speaker)
- Reviewer: none yet
- Date:
- Dialect / spelling notes:
- Meaning matches the English prompt:
- Issues found:

Checklist:

- [ ] Wording is natural for a native speaker, not translationese
- [ ] Same requirements as `prompts/en.md`: nothing added, nothing dropped
- [ ] Identifiers, file names, class names and attribute names (`data-testid`, `dir`, `dist/app.css`, `src/input.css`) match the fixture exactly
- [ ] File is UTF-8, no BOM, bidi control characters intact

## Fixture content for native review

The page text below was drafted by an agent and is not reviewed. Strings shared with `rtl-tailwind-sidebar` (لوحة التحكم, الطلبات, الطلبات الجديدة, آخر تحديث اليوم) were copied from that fixture. Each string must read as natural Modern Standard Arabic (or Jordanian where it fits) in a real settings screen. A string the board changes must be changed in `fixture/` and in its byte copy `tests/pristine/` in the same pull request (a repo test checks the two are identical). The grader compares testid text with the pristine copy at grade time, so no digest needs regenerating.

| Arabic string | File |
|---|---|
| لوحة التحكم | all three pages (brand) |
| الملف الشخصي | all three pages (nav), index.html (title) |
| الإشعارات | all three pages (nav), notifications.html (title) |
| الفوترة | all three pages (nav), billing.html (title) |
| البريد الإلكتروني | index.html |
| اللغة | index.html |
| العربية | index.html |
| أكمل ملفك الشخصي | index.html |
| حفظ | index.html |
| الكل | notifications.html |
| غير مقروءة | notifications.html |
| الطلبات | notifications.html |
| الطلبات الجديدة | notifications.html |
| آخر تحديث اليوم | notifications.html |
| رابط الإشعارات | notifications.html |
| الخطة الحالية | billing.html |
| رقم الحساب | billing.html |
| البطاقة | billing.html |
| التاريخ | billing.html |
| المبلغ | billing.html |
| تنزيل | billing.html |

## Notes and known grader limits

- Checks run on all three pages; keys are `<page>.<check>`. Library checks: `root_dir_lang`, `islands_direction` (`computed_direction`, want `ltr`), `no_physical_tailwind`, `no_physical_css`, `no_horizontal_overflow_360`. Task-local (`tests/verify.py`): `rtl_mirrors_ltr`, `testids_and_text_kept`, `ltr_layout_unchanged`, `ltr_styles_unchanged`, `ltr_islands_kept`, `css_from_build` (11 per page, 33 in all). `css_from_build` is not in the design's check list; it is carried from `rtl-tailwind-sidebar` because the design's anti-goals need `<style>` and inline-style cheats to score 0.
- `ltr_layout_unchanged` and `testids_and_text_kept` render the untouched fixture (`tests/pristine/`, built by `build.sh` into `OUT/pristine.css`) in a second page of the same browser, with the agent's `<html lang>` and `dir="ltr"`, so expected boxes are measured at grade time and never appear in the prompt. Boxes (left, top, width) are compared per testid and occurrence, and every element that has a class in the fixture keeps its left, top, width and height, matched by its tag/nth-of-type path from `<body>`. A fixture path missing from the page fails both `ltr_layout_unchanged` and `ltr_styles_unchanged`, and the page side is snapshotted over every element, so an element whose class was removed still matches. Restructuring (adding, removing, reordering or re-tagging elements) is out of bounds by the prompt, so this is fair: a probe that wraps the reference's avatar row in a flex `<div>` fails both checks, as does deleting the IBAN island. Failure details print only the agent's value, never the expected one.
- `ltr_styles_unchanged` (CTO decision 2026-11-16): with `dir="ltr"`, every element that has a class in the fixture (matched by path) keeps the pristine render's computed padding, border widths, border colours (on sides that have a border), corner radii and scroll-padding per physical side, and its text-align with `start`/`end` resolved to left/right. Margins and inset are graded through the element boxes in `ltr_layout_unchanged` instead of as values, so a correct solution that swaps a margin for `gap` or a float for flex (`flex_and_gap`) still scores 1. Gaming cases that drop or misplace a utility without moving a box fail this key alone: `wrong_side_nav_border`, `drop_border_colour`, `drop_plan_radius` (plus the per-page mutations: tip radius, `scroll-ps-4`, `text-end` on the amount column).
- Accepted limit: hover and other state-only styles (`hover:border-s-slate-300`, `hover:border-e-2`) are not rendered, so dropping or flipping them is not graded. They are still caught when left physical (`no_physical_tailwind`, `no_physical_css`).
- `ltr_islands_kept` measures where the island's text starts (a DOM Range) against its left content edge in the Arabic page. Islands are text elements, not inputs. `islands_direction` checks computed `direction: ltr` separately, so each fails alone under its own mutation (the `ltr_islands_kept` mutation uses `rtl:text-end`, which changes only the Arabic page).
- One `app.css` serves all three pages, so a physical rule in it fails `no_physical_css` on every page (accepted, CTO decision 2026-11-16); a physical class on one page fails `no_physical_tailwind` on that page only. `hover:border-r-2` is caught by both checks (the static pass reads the compiled `:hover` rule).
- `rtl_mirrors_ltr` (CTO decision 2026-11-16, after QA found unmirrored Arabic pages scoring 1) replaces the library's `mirror_on_dir_flip`, which graded three elements per page and is a strict subset. On the agent's own page (no fixture values), every element under `<body>` must mirror when `<html dir>` flips: `left_rtl = W - left_ltr - width`, same top, width and height (2 px), and padding, border widths, border colours (on sides with a border), corner radii and scroll-padding equal the LTR values with left and right swapped, and text-align (start/end resolved) swaps. Exclusions: elements with an empty box in both directions (`display: none`) are skipped; a left-to-right island (an element with its own `dir`) only mirrors its box, and its descendants are skipped. It is graded at 1280 px only, where no scroller on these pages overflows. Gaming cases: `[dir=rtl] table, [dir=rtl] [data-testid=filters] { direction: ltr }` (`rtl_direction_ltr_hack`) and `rtl:` variants that put the tip's border, padding and alignment back on the left (`rtl_variant_wrong_side`) both score 0.
- Gaming cases covered, in `tests/rtl_gaming/rtl-tailwind-logical-convert/`: hand-edited `dist/` (`dist_only_edit`), physical utility behind `ltr:` (`ltr_variant`), deleted island (`delete_island`), transparent island (`hide_island`), scaled main area (`shrink_main`), `<style>` element (`style_element`), body flipped with `scaleX(-1)` on the untouched fixture (`fresh_mirror_body`), nav accent border on the wrong side (`wrong_side_nav_border`), dropped border colour (`drop_border_colour`), dropped plan-card radii (`drop_plan_radius`), a classless wrapper around the sidebar and main that shifts every path while a border colour is dropped (`wrapper_hides_styles`), a script that removes itself (`self_removing_script`), `dir` and `lang` set by such a script (`dir_lang_by_script`), parts of the Arabic page forced back to `direction: ltr` (`rtl_direction_ltr_hack`) and `rtl:` variants on the wrong side (`rtl_variant_wrong_side`). Inline `style` is the `css_from_build` mutation. Alternatives that must pass: arbitrary logical properties plus hand-written logical CSS (`logical_properties`), flex and `gap` in place of float and margins with `inset-s-*` and `lang="ar"` (`flex_and_gap`).
- The known-bad solution (regex pass on two pages, islands flipped to `rtl`) fails 16 checks across the three pages; `billing.ltr_islands_kept` passes for it because billing keeps its physical `text-left`.
- A leftover file in `/app` that mentions physical class names (for example a `.py` conversion script) is compiled by Tailwind's source scan and fails `no_physical_css` on all three pages; the prompt says so. An `index.html.bak` copy of the fixture was not picked up in the probe.
- `css_from_build` parses each page's source HTML (as `rtl-contact-page-build`'s `static_page` does) and fails on any `<script>`, frame, plugin, template or base element, `on*` handler or `javascript:` URL, and checks the live DOM for the same, so a script that removes itself, or sets `dir` and `lang` and then removes itself, scores 0 (QA found both scored 1 at 4c91b8e, when only the live DOM was checked). The grader trusts the in-container Chromium, Python and Tailwind CLI (see `tasks/SCHEMA.md`).

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
