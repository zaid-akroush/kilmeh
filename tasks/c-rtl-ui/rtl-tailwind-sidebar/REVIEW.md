# Native-review record: rtl-tailwind-sidebar

Task version: 0.1.0. Process: see `tasks/REVIEW_PROCESS.md`.

`review_status` in `task.toml` is set only by a native speaker, never by an agent. The `levantine` prompt was drafted by an agent (style modelled on public Jordanian developer posts, nothing copied) and approved unchanged by the board, a native Jordanian speaker, on 2026-11-21. Its hash is pinned in `tests/test_rtl_vendoring.py`. Prompts are short; the full requirements (English, identical for every variant) are in `fixture/SPEC.md`. Fixture Arabic still needs native review.

## Variants

| Variant | File | Kind | review_status (task.toml) |
|---|---|---|---|
| en | prompts/en.md | en | draft (AI-written) |
| levantine | prompts/levantine.md | dialect (levantine, Arabic script) | native_reviewed (AI draft, board-approved 2026-11-21) |

## Variant: levantine

Filled 2026-11-21: an AI draft that the board (native Jordanian speaker) approved unchanged; hash pinned in `tests/`. Not yet checked by a second native speaker.

- Requirements to carry over (all are graded): an Arabic `lang` (`ar` or `ar-JO`) and right-to-left on `<html>`; the sidebar at the right edge, the main content entirely to its left, the sidebar visible and about 16rem wide, nothing hidden, clipped, shrunk or scaled; the layout follows `<html dir>` alone and uses Tailwind logical utilities, with no physical utility even behind `rtl:` or `ltr:`, and no physical CSS property anywhere in the compiled CSS (`@apply`, arbitrary values, hand-written rules and `@import`ed styles included, checked by `no_physical_css` on the built CSS); no sideways scrolling at 360 px; all styling from Tailwind classes and `src/input.css`, the page linking only `dist/app.css` (no `<style>`, no `style` attribute, no other stylesheet, no `<script>`), and `dist/` is rebuilt by the grader so editing it has no effect; every `data-testid` element kept, visible, with its Arabic text unchanged.
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

The page text below was drafted by an agent and is not reviewed. Each string must read as natural Modern Standard Arabic (or Jordanian where it fits) in a real dashboard. A string the board changes must be changed in the fixture in the same pull request, and `TEXT_DIGEST` in `tests/verify.py` regenerated (a repo test checks it against the fixture).

| Arabic string | File |
|---|---|
| لوحة التحكم | index.html |
| الرئيسية | index.html |
| الطلبات | index.html |
| المنتجات | index.html |
| الإعدادات | index.html |
| نظرة عامة | index.html |
| جديد | index.html |
| المبيعات | index.html |
| الطلبات الجديدة | index.html |
| العملاء | index.html |
| آخر تحديث اليوم | index.html |

## Notes and known grader limits

- `tests/verify.py` pins the text of every `data-testid` element (`TEXT_DIGEST`) and the count of each testid, so the Arabic text and markup hooks must stay. The digest is checked against the fixture by `tests/test_rtl_vendoring.py`.
- `build.sh` rebuilds `app.css` from the agent's source with the pinned Tailwind CLI (v4.3.3, sha256 per architecture in `environment/Dockerfile`) into a scratch directory, and `verify.py` serves that file in place of `/dist/app.css`. The `dist/` an agent leaves behind is never graded.
- `main_beside_sidebar` (task-local) also requires the sidebar to stay at least 200 px wide and the main box at least 300 px wide at 1280 px, so hiding, collapsing or scaling the sidebar down does not pass. The fixture's page has no breakpoint-specific layout: `md:` and other variants are allowed.
- `no_physical_css` runs on the page with the built CSS (Tailwind preflight needs no allow-list entries). Gaming cases covered, all in `tests/rtl_gaming/`: hand-edited `dist/`, hidden sidebar, `overflow-x: hidden`, `transform` and `zoom` shrinking, extra stylesheet, inline style, deleted text, physical rules keyed on `[dir]` in `input.css` (`fresh_handcss`), `@apply` of physical utilities (`fresh_applycss`), `@import url(data:...)` of physical rules (`fresh_dataimport`), physical utilities behind `ltr:` (`fresh_ltrvariant`) and physical shorthands in arbitrary values (`fresh_insetshorthand`). Alternatives that must pass: grid layout, component CSS, arbitrary logical properties, flex with `lang="ar"`, `inset-s-*`/`inset-e-*`, a redundant `rtl:` variant, a relative stylesheet href.
- `dir` and `lang` set by JavaScript at load time are not possible here (`<script>` is banned by `css_from_build`).
- The grader trusts the in-container Chromium and Python, the same tampering limit as the other tracks (see `tasks/SCHEMA.md`).
- The image build downloads the Tailwind binary in a build stage (`debian:bookworm-slim` with `apt-get install curl ca-certificates`); only the sha256-verified binary is copied into the final image. The apt packages themselves are not pinned.

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
