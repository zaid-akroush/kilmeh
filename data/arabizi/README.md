# Arabizi answer key

Pairs of Arabizi (Arabic in Latin letters) and the correct Arabic, used to score any Arabizi
converter. Jordanian first. Licence: `LICENSE.md` (CC BY 4.0).

**Only native speakers write pair text.** Agents write code, formats and English copy, never an
Arabizi or Arabic answer-key sentence. Text is stored byte-for-byte: no normalising, trimming or
reordering. Hashes of committed pairs are pinned in `tests/`.

## Layout

```text
key/v1/train.jsonl   pairs a converter may learn from
key/v1/test.jsonl    pairs used only for scoring
template/            empty files for the board to fill (empty text allowed only here)
mapping.toml         letter -> Arabic candidate table (AI draft, board edits)
heldout/             private pairs, git-ignored, never published
```

Published versions are never edited in place. Corrections go in `key/v2/` with a changelog note.

## Fields (one JSON object per line, UTF-8, no BOM, LF)

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | unique across all files, e.g. `jo-0001` |
| `arabizi` | yes | the sentence in Latin letters and digits; no Arabic-script characters |
| `arabic` | yes | the correct Arabic; at least one Arabic letter |
| `dialect` | yes | `levantine`, `gulf`, `egyptian`, `maghrebi`, `iraqi`, `sudanese` or `other` (as in `tasks/SCHEMA.md`) |
| `country` | yes | country code, e.g. `JO` |
| `source` | yes | `board` or `site` |
| `authors` | yes | `1` or `2` (two natives agreed or wrote variants) |
| `alt_arabic` | no | list of other correct spellings, so a valid variant is not punished |
| `notes` | no | free text |

Template files (`template/*.jsonl`) have only `id`, `scenario`, `arabizi`, `arabic`; `scenario`
is an English hint for the writer.

## Split rule

A pair's file is decided by its `id` alone: `sha256(id as UTF-8)`; if the first byte is below 51 the
pair belongs in `test.jsonl` (about 20%), otherwise in `train.jsonl`. Adding pairs never moves
existing ones. A pair in the wrong file is an error. The function is `split_of` in
`src/kilmeh/arabizi_key.py`.

## Adding pairs

1. A native speaker supplies `arabizi` and `arabic` (board, or consenting website contributor).
2. Insert the text byte-for-byte into a new line with a fresh `id`; do not retype or fix it.
3. Put the line in `train.jsonl` or `test.jsonl` as `split_of(id)` says.
4. Run `uv run kilmeh validate-arabizi data/arabizi` (exit 0 required) and pin the new hashes in
   `tests/`.
