# Native-review record: rtl-nav-fix

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

| Arabic string | File |
|---|---|
| مكتبة النور | index.html |
| الرئيسية | index.html |
| الكتب | index.html |
| اتصل بنا | index.html |
| تسجيل الدخول | index.html |
| اقرأ أكثر كل يوم | index.html |
| اكتشف مجموعة واسعة من الكتب العربية بأسعار مناسبة | index.html |
| جميع الحقوق محفوظة | index.html |

## Notes and known grader limits

- The page is in two directions: `lang="ar-JO"` and `dir="rtl"` are set on `<html>` by the reference solution (the fixture ships `lang="en"` and no `dir`).
- `mirror_on_dir_flip` only grades asymmetric boxes (logo, nav, sign-in button, hero title), because a box centred on the page mirrors onto itself under any layout.
- `computed_direction` is checked on `body` and `footer`. The footer is not used by any other check, which keeps its isolation test exact.
- Known limits (tickets, not fixed): physical CSS inside a closed shadow root is invisible to `no_physical_css`; `dir` and `lang` set by JavaScript at load time are accepted, because the check reads the DOM after load.
- The grader trusts the in-container Chromium and Python, the same tampering limit as the other tracks (see `tasks/SCHEMA.md`).

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
