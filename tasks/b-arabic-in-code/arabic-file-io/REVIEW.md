# Native-review record: arabic-file-io

**2026-11-21:** the `en` and `levantine` prompts are AI drafts that the board (native Jordanian speaker) approved unchanged in chat. Hashes are pinned in `tests/`. Per the process, the board sets `review_status` itself. Fixture Arabic still needs native review.

Task version: 0.1.0. Process: see `tasks/REVIEW_PROCESS.md`.

`review_status` in `task.toml` is set only by a native speaker, never by an agent. No second native speaker has checked this task yet.

## Variants

| Variant | File | Kind | review_status (task.toml) |
|---|---|---|---|
| en | prompts/en.md | en | draft (AI-written) |
| levantine | prompts/levantine.md | dialect (levantine, Arabic script) | draft (AI draft, board-approved in chat 2026-11-21) |

## Variant: levantine

Filled 2026-11-21: an AI draft that the board (native Jordanian speaker) approved unchanged in chat; hash pinned in `tests/`. `review_status` stays `draft` until the board sets it in the v1.1 review. Not exported or run in v1.0.

- Author: (board, native speaker)
- Reviewer: none yet
- Date:
- Dialect / spelling notes:
- Meaning matches the English prompt:
- Issues found:

Checklist:

- [ ] Wording is natural for a native speaker, not translationese
- [ ] Same requirements as `prompts/en.md`: nothing added, nothing dropped
- [ ] Identifiers and names (`ingest.py`, `IN_DIR`, `OUT_DIR`, `summary.json`, `products.csv`, `legacy.csv`, `config.json`, `docs/`, `.summary.txt`, `cp1256`, `BOM`) match the fixture exactly
- [ ] File is UTF-8, no BOM
- [ ] Says the same things as the English prompt about the unprivileged user and standard library only

## Fixture content for native review

The fixture (`fixture/sample/`) and the grader's word pools (`tests/verify.py`) hold ordinary Arabic words as data: product names, city names, shop titles, document names and sentences. All are encodable in Windows-1256 where required. The board should confirm each word is natural and carries no unwanted meaning.

## Notes and known grader limits

- The agent's `ingest.py` runs as uid 65534 in its own session with a 30 s limit, on inputs the grader writes per run (words drawn with SystemRandom). `tests/verify.py` holds the pools and the expected values. `test.sh` locks `/tests` first, and verify refuses to grade if anything under it is reachable by another user.
- The output directory is writable by the agent's script, so output files are read without following links, as regular files only (at most 50 doc files, 1 MB each).
- File names are compared as raw UTF-8 bytes, so a normalized name (NFD) or a name with lost characters fails `doc_filenames_arabic`.
- Locale: the script runs with `-X warn_default_encoding -W error::EncodingWarning`, so a text `open()` without `encoding=` crashes. A non-UTF-8 locale is not used because it would also break Arabic file names (the filesystem encoding), which the task does not ask the agent to handle.
- Known limit: the script runs with no network sandbox of its own (the container's network is already off per `tasks/SCHEMA.md`).
- Remaining limit: grading runs in the solution's own container, so a root `solve.sh` could tamper with `python3` or the stdlib before grading (see `tasks/SCHEMA.md`, Known limits).

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
