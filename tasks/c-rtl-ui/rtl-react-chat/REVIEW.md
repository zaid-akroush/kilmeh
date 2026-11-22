# Native-review record: rtl-react-chat

Task version: 0.1.0. Process: see `tasks/REVIEW_PROCESS.md`.

`review_status` in `task.toml` is set only by a native speaker, never by an agent. The `levantine` prompt was drafted by an agent (style modelled on public Jordanian developer posts, nothing copied) and approved unchanged by the board, a native Jordanian speaker, on 2026-11-21. Its hash is pinned in `tests/test_rtl_vendoring.py`. Prompts are short; the full requirements (English, identical for every variant) are in `fixture/SPEC.md`. Fixture Arabic still needs native review.

## Variants

| Variant | File | Kind | review_status (task.toml) |
|---|---|---|---|
| en | prompts/en.md | en | draft (AI-written) |
| levantine | prompts/levantine.md | dialect (levantine, Arabic script) | native_reviewed (AI draft, board-approved 2026-11-21) |

## Variant: levantine

The file holds only `TODO(board): native Jordanian prompt, see REVIEW.md`. An agent never writes this prompt. The board writes it in Jordanian (Levantine) Arabic with the same requirements as `prompts/en.md`, then sets `review_status` and fills in the section below. `--strict` fails until then.

- Requirements to carry over, all graded:
  - the chat convention: own messages (`bubble-me`) on the left half of the screen, incoming messages (`bubble-them`) on the right half, every bubble. **The board may correct this convention** (the CTO kept "own on the left in an RTL chat"); if it changes, `tests/verify.py` and the mutations change with it.
  - each avatar at the start (right) side of its incoming bubble;
  - the product name and order number isolated from the Arabic around them;
  - the composer follows what is typed (Arabic reads right to left, Latin left to right);
  - everything mirrors when only `<html dir>` changes, with logical values and no physical left or right (in the stylesheet or inline styles);
  - the order details card fits 360 px with no hidden overflow, no `transform` or `zoom` shrinking, and is not collapsed (`card_fits`);
  - the graded page is a fresh build of `src/` with the image's own toolchain (edits to `dist/` and `node_modules/` do not count); `index.html` has exactly one `<script src="/dist/app.js">`, no inline code, no `on*=` attributes, no `javascript:` URLs; `lang` is `ar` or `ar-JO`; the card is at least 200 px wide.
- Author: (board, native Jordanian speaker)
- Reviewer: none yet
- Date:
- Dialect / spelling notes:
- Meaning matches the English prompt:
- Issues found:

Checklist:

- [ ] Wording is natural for a native speaker, not translationese
- [ ] Same requirements as `prompts/en.md`: nothing added, nothing dropped
- [ ] Identifiers, file names and attribute names (`data-testid`, `dir`, `dist/app.js`) match the fixture exactly
- [ ] File is UTF-8, no BOM, bidi control characters intact

## Fixture content for native review

The page text below was drafted by an agent and is not reviewed. Each string must read as natural Modern Standard Arabic (or Jordanian where it fits) in a real page. A string the board changes must be changed in the fixture (`src/Chat.jsx`) in the same pull request, and `tests/composer_sample.txt` plus its pinned hash in `tests/test_rtl_vendoring.py` if it is the composer placeholder.

| Arabic string | File |
|---|---|
| خدمة العملاء | src/Chat.jsx (header, "customer service") |
| مرحباً، كيف يمكنني مساعدتك؟ | src/Chat.jsx (incoming message) |
| اشتريت هاتف iPhone 17 من متجركم | src/Chat.jsx (own message; the Latin run `iPhone 17` is the product) |
| رقم طلبك هو ORD-48213 وهو في الطريق إليك | src/Chat.jsx (incoming message; the Latin run `ORD-48213` is the order number) |
| تفاصيل الطلب | src/Chat.jsx (order card title) |
| شكراً، سأنتظر | src/Chat.jsx (own message) |
| اكتب رسالتك | src/Chat.jsx (composer placeholder) |
| إرسال | src/Chat.jsx (send button) |

## Notes and known grader limits

- `tests/composer_sample.txt` is the Arabic typed into the composer. It is copied from the composer's `placeholder` in `src/Chat.jsx` byte for byte (21 bytes, sha256 pinned in `tests/test_rtl_vendoring.py`), never retyped.
- The task needs Node at build time. The Playwright base image has none, so the Dockerfile copies `node` and `npm` from a digest-pinned `node:22` build stage, where `npm ci --ignore-scripts` also installs the exact packages in `fixture/package-lock.json`. esbuild's platform binary is an optional package that `npm ci` selects for the build platform (verified for linux amd64 and arm64); there is no network at grade time.
- `tests/build.sh` rebuilds from `src/` into `/tmp` with `--outdir` (`app.js`, plus `app.css` when CSS is imported from JS); `verify.py` serves them in place of `/dist/app.js` and `/dist/app.css`, so a hand-edited or stale `dist/` never counts (a solution that forgot to rebuild still scores, because grading builds fresh).
- The grading toolchain is a second copy of the same `npm ci` output at `/opt/kilmeh-build/node_modules`; `build.sh` runs esbuild from there and pins `react`, `react-dom` and `scheduler` to it with `--alias`, so replacing or editing `/app/node_modules` changes nothing (`/app/node_modules` stays for the agent's own builds). `toolchain_intact` recomputes sha256 of esbuild (shim and platform binary), react, react-dom and scheduler with `/opt/kilmeh-build/digest.py` and compares them with `/opt/kilmeh-build/DIGESTS`, recorded when the image was built (computed in the Docker build, not pinned in a test, because the esbuild binary differs per architecture; the lockfile's sha512 integrity already pins the packages themselves). **Known limit:** a solution that runs as root could still edit `/opt` and DIGESTS together; that is the existing in-container tampering limit.
- `index_html_static` is an allow-list over the served `index.html` bytes, read before any JS runs: elements `html`, `head`, `meta` (charset or `name=viewport` only), `title`, at most one `link rel=stylesheet` to `/dist/app.css` or the source `/src/styles.css` (the fixture links the latter, so both are allowed), exactly one `script` with `src` resolving to `/dist/app.js` and no inline content, `body`, and one root `div` with only an `id`; attributes per element are listed in `verify.py`; text may only be whitespace (and the title). Everything else fails (iframe, object, embed, template, svg, base, other links, `meta http-equiv`, `on*=`, `javascript:`). `requests_allowed` opens a second page in the same sandbox context with request events attached before navigation: only `/index.html`, `/dist/app.js` and the stylesheet may be requested, no extra frame, no other document request, and nothing off-origin (what the sandbox aborts). `bundle_is_built_output` still checks the live DOM.
- `build.sh` copies only `/app/src` (symlinks followed) into a fresh temp directory and runs the `/opt` esbuild there with `--tsconfig-raw='{}'`, `--jsx=automatic --jsx-import-source=react` and the aliases, so no `package.json`, `tsconfig.json` or `jsconfig.json` from `/app` and no `/app/node_modules` can affect the bundle (gaming cases `fresh_tsconfig_jsximport` and `fresh_package_json_browser`). Consequence: source may only import react, react-dom, scheduler and files inside `src/`.
- `card_fits` is task-local (not in the shared library): `fits_width` plus no transform, scale, rotate, translate or zoom on the card or its ancestors, drawn width equal to layout width, and at least 200 px wide.
- `bubbles_me_left`, `bubbles_them_right` and `avatar_at_start` are task-local and look at every bubble and avatar, not the first match, so a hidden or decoy element cannot score. Hidden (display, visibility, opacity, zero size) or off-screen bubbles fail.
- `dir`/`lang` set by JavaScript at load time are accepted (the checks read the DOM after load); physical CSS inside a closed shadow root is invisible to the CSS checks. The grader trusts the in-container Chromium, Node and `node_modules`, the same tampering limit as the other tracks (see `tasks/SCHEMA.md`).
- Chat message order, dates and times are fixed fixture data (`10:02` to `10:05`), not graded.

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
