# Native-review record: rtl-contact-page-build

Task version: 0.1.0. Process: see `tasks/REVIEW_PROCESS.md`.

`review_status` in `task.toml` is set only by a native speaker, never by an agent. The `levantine` prompt was drafted by an agent (style modelled on public Jordanian developer posts, nothing copied) and approved unchanged by the board, a native Jordanian speaker, on 2026-11-21. Its hash is pinned in `tests/test_rtl_vendoring.py`. Prompts are short; the full requirements (English, identical for every variant) are in `fixture/SPEC.md`. Fixture Arabic still needs native review.

## Variants

| Variant | File | Kind | review_status (task.toml) |
|---|---|---|---|
| en | prompts/en.md | en | draft (AI-written) |
| levantine | prompts/levantine.md | dialect (levantine, Arabic script) | native_reviewed (AI draft, board-approved 2026-11-21) |

## Variant: levantine

The file holds only `TODO(board): native Jordanian prompt, see REVIEW.md`. An agent never writes this prompt. The board writes it in Jordanian (Levantine) Arabic with the same requirements as `prompts/en.md`, then sets `review_status` and fills in the section below. `--strict` fails until then.

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

| Arabic string | First seen in |
|---|---|
| اتصل بنا | known-bad/solve.py |
| شركة الأفق | known-bad/solve.py |
| الرئيسية | known-bad/solve.py |
| خدماتنا | known-bad/solve.py |
| تواصل معنا | known-bad/solve.py |
| للاستفسار اتصل بنا على الرقم | known-bad/solve.py |
| أو راسلنا على | known-bad/solve.py |
| الاسم | known-bad/solve.py |
| البريد الإلكتروني | known-bad/solve.py |
| رقم الهاتف | known-bad/solve.py |
| التالي | known-bad/solve.py |
| مزيد | rtl-contact-page-build/qa_f03_details.py |
| نص إضافي | rtl-contact-page-build/qa_f03_details.py |
| مكتب النور | rtl-contact-page-build/qa_faira.py |
| البداية | rtl-contact-page-build/qa_faira.py |
| من نحن | rtl-contact-page-build/qa_faira.py |
| تواصل | rtl-contact-page-build/qa_faira.py |
| راسلنا | rtl-contact-page-build/qa_faira.py |
| يمكنك الاتصال على | rtl-contact-page-build/qa_faira.py |
| أو مراسلتنا عبر | rtl-contact-page-build/qa_faira.py |
| في أي وقت | rtl-contact-page-build/qa_faira.py |
| البريد | rtl-contact-page-build/qa_faira.py |
| الهاتف | rtl-contact-page-build/qa_faira.py |
| متابعة | rtl-contact-page-build/qa_faira.py |
| دار الكلمة | rtl-contact-page-build/qa_fairb.py |
| الأولى | rtl-contact-page-build/qa_fairb.py |
| الثانية | rtl-contact-page-build/qa_fairb.py |
| الثالثة | rtl-contact-page-build/qa_fairb.py |
| للتواصل | rtl-contact-page-build/qa_fairb.py |
| شركة | rtl-contact-page-build/fresh_qa_a12_transparent_arabic.py |
| ش.أ | rtl-contact-page-build/fresh_qa_a15_dup_logo_realleft.py |

## Notes and known grader limits

- The task is graded on a page the agent writes from scratch, so the grader also guards against gaming (all in `tests/verify.py`): `elements_fit` (every listed element exists exactly the stated number of times, and is seen: it has a size, is not hidden or transparent, is not clipped by an overflow container, is not covered or masked (`elementFromPoint` at its centre returns it or something inside it), and starts within the first 3 screens), `no_shrink_tricks` (no zoom or transform scale, text at least 12 px), `arabic_text` (logo, each nav link, the next button and the contact text each hold visible Arabic text; hidden, transparent, covered, alt-only or screen-reader-only text does not count, so an image logo with a sr-only Arabic label fails), `static_page` (the HTML, SVG and XML files are parsed: no script, iframe, frame, object, embed, template, base, `on*` attribute or `javascript:` URL; comments are ignored; the DOM is checked too) and `svg_markup_unchanged` (the arrow SVG from `README.md` stays as shipped, so it is flipped with CSS). Three more checks run at both widths (keys `_1280` and `_360`, one isolation mutation each): `no_overlays` (no fixed or absolute, pointer-events:none, painted element or ::before/::after over a listed element; `elementFromPoint` ignores those), `no_effects` (no filter, backdrop-filter or mix-blend-mode on a listed element or its ancestors) and `readable_contrast` (WCAG 3:1 against the first non-transparent ancestor background, white by default; text colour alpha above 0.5). The Arabic-text rule also needs the text's own client rects to lie inside the screen and inside every overflow ancestor (`text-indent: -9999px` fails); its gaming case is the isolation proof for that part, folded into the `arabic_text` check.
- `tests/name_sample.txt` is the Arabic name typed into the name field. It is a byte copy of `rtl-order-summary-fix/tests/name_sample.txt` (sha256 pinned in `tests/test_rtl_vendoring.py`), never retyped.
- The prompt states every graded requirement; the board's Arabic prompt must keep all of them: RTL attributes in the HTML source, visible Arabic text in the five listed places, logical CSS, the 360 px fit with no overflow hiding and no hiding of elements, the definition of visible and the 3-screens rule, exactly one element per `data-testid` (three `nav-link`), no overlays or effects, 3:1 contrast, no zoom or transform scale, 12 px text, the arrow flipped with CSS using the SVG unchanged, and the static-page rule.
- Correct pages written in other ways must also score 1: two alternatives, `alt_grid` and `alt_float`, and QA's fair pages and variants (`qa_*`, in `tests/rtl_alternatives/`). The gaming and decoy attempts in `tests/rtl_gaming/` must not.
- Accepted limits (tickets, not fixed): `@keyframes` and `background-position` are not graded; a phone number repeated as plain text next to the isolated graded run is not detected (QA case a16, kept as a fair alternative); contrast ignores background images and gradients; QA's fair pages use the darker logo green `#067a38` because the old `#0b5` is 2.55:1 on white and fails the 3:1 rule.
- The image installs `playwright`, `pyee`, `greenlet` and `typing-extensions` with `pip --require-hashes --no-deps` from hashes copied from `uv.lock`, on a digest-pinned base image.
- The grader trusts the in-container Chromium and Python, the same tampering limit as the other tracks (see `tasks/SCHEMA.md`).

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
