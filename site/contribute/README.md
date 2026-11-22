# Contribute words (static site)

A small public page where native Arabic speakers write Arabic and Arabizi spellings
of English words, so Kilmeh covers dialects its maintainers cannot write themselves.
Plain HTML, CSS and JS modules: no framework, no build step, no CDN, no npm
dependencies. It can be hosted on GitHub Pages as is.

## Run locally

```
cd site/contribute
python3 -m http.server 8000
```

Open <http://localhost:8000/>. Without `config.js` the page runs in **test mode**
(banner "Test mode: nothing is sent to a server"): submissions go only to the browser
console and `sessionStorage` (key `kilmeh.contribute.mock-submissions`), where the
name and email are replaced by `name_given` / `email_given` flags. `?mock=1` forces test
mode; `?lang=ar` opens the Arabic UI. Opening `index.html` from disk (`file://`)
does not work, because the page fetches its JSON files.

## Releases: bump the version string

The host caches every file for 10 minutes (`max-age=600`), so a visitor can get a new
`index.html` with an old `styles.css` or module. `index.html` and every `import` in `js/`
therefore carry `?v=<version>` (now `2026-11-12e`). **On every release, change that one
string everywhere** (`grep -rn "v=2026" site/contribute`); a test checks they all match.
JSON and Markdown fetches already use `cache: "no-cache"`.

## Files

| File | What |
|---|---|
| `index.html`, `styles.css`, `js/` | the page (`js/logic.js` holds all pure logic) |
| `words.json` | the 100-word pool (English only) |
| `strings.en.json` / `strings.ar.json` | UI strings; same keys. The Arabic is AI-drafted, board review pending: see `ARABIC_REVIEW.md` |
| `privacy.en.md` / `privacy.ar.md` | privacy notice (Arabic is an AI draft, board review pending) |
| `ARABIC_REVIEW.md` | every Arabic string next to its English source, for board review |
| `fonts/` | self-hosted woff2 fonts and their licences (see Fonts) |
| `config.example.js` | copy to `config.js` (git-ignored) with Supabase URL and anon key |
| `supabase/schema.sql`, `supabase/README.md` | database, access rules, setup, export and deletion steps |
| `tests/logic.test.js`, `tests/api.test.js` | `node --test tests/logic.test.js tests/api.test.js` (also run by `uv run pytest`); the API tests use a stubbed `fetch`, no network |
| `../../tests/test_contribute_site_db.py` | runs `schema.sql` on postgres:16 in Docker (anon, authenticated, service_role roles); opt-in: `KILMEH_DOCKER_TESTS=1 uv run pytest tests/test_contribute_site_db.py` |

## Flow

1. Intro: explanation, optional name and email, required country of the person's
   Arabic (22 countries plus Other with free text; the dialect group is derived
   from it, see `COUNTRY_DIALECT` in `js/logic.js` and
   `kilmeh_private.dialect_of` in `supabase/schema.sql`), optional "credit me by
   name" (needs a name), required
   consent.
2. Ten words, one at a time: Arabic (required unless "keep in English"), Arabizi
   (required), feminine pair for gendered words, up to 3 skips per batch, Back, a
   2-second minimum per new word. Progress survives a refresh (`sessionStorage`).
3. After the tenth word the contributor row (first batch only) and the 10 entries
   are sent, then a thank-you screen shows the deletion code and "Add 10 more
   words". Nothing is sent before the tenth word. Once the contributor row is
   accepted, the intro details are locked for the session; a failed entries send is
   retried without resending them.

Gendered words show an optional feminine pair. `gendered` is true when the Arabic
normally changes with the gender of the person addressed (including imperative
buttons such as Save or Send) or of the speaker (such as Sorry); `gender_note`, when
present, replaces the generic hint above the feminine fields.

## Before launch (board)

- Review every Arabic line in `ARABIC_REVIEW.md`, `strings.ar.json` and `privacy.ar.md` (AI draft).
- Supabase project, `config.js` and the CSP `connect-src`: see `supabase/README.md`.

## Look and fonts

The page uses one look, "Ink and paper": warm paper, ink, terracotta, eight-point
stars. Fonts are self-hosted (no CDN) and licensed under the SIL Open Font License 1.1;
the licence texts sit next to them in `fonts/`. Total about 306 KB; system fonts are
the fallback.

| Font | Used for | Licence |
|---|---|---|
| Amiri 400 and 700 (Arabic and Latin) | wordmark, headings, the word, Arabic answers, English text | `fonts/OFL-Amiri.txt` |
| Cairo 400 and 700 (Arabic and Latin) | Arabic body text, labels and buttons (clear at phone sizes) | `fonts/OFL-Cairo.txt` |
