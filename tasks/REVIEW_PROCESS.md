# Prompt review process

1. A variant starts as `draft` (AI-written or unreviewed). If the author is a native speaker who wrote the text themselves, they set `native_authored`.
2. A second native speaker checks it and sets `native_reviewed`. Whoever changes `review_status` records who and when in the task's `REVIEW.md`.
3. Dialect and Arabizi variants must be native-authored or native-reviewed; they are never machine-written alone.
4. `--strict` rejects every prompt that is still `draft`.
5. Every Arabic prompt must still be checked by a native speaker before release, and `uv run kilmeh validate-tasks --strict tasks` must pass. **v1.0 exception (maintainer decision, 2026-11-22):** v1.0 ships before the full native review, so it does not pass `--strict`. Prompts still marked `draft` stay labelled `draft`. `kilmeh export-harbor` skips draft Arabic prompts, so no draft Arabic text was run in v1.0. `--strict` is required from v1.1.
