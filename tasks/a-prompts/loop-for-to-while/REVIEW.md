# Native-review record: loop-for-to-while

Task version: 0.1.0. Process: see `tasks/REVIEW_PROCESS.md`.

`review_status` in `task.toml` is set only by a native speaker, never by an agent: `native_authored` by a native author who wrote the text, `native_reviewed` by a second native speaker who checked it. Record who and when below.

No second native speaker has reviewed any of the three variants yet. All three are `native_authored`, none is `native_reviewed`.

## Variants

| Variant | File | Kind | review_status (task.toml) |
|---|---|---|---|
| en | prompts/en.md | en | native_authored |
| arabizi_levantine | prompts/arabizi_levantine.md | dialect (levantine, latin script) | native_authored |
| levantine | prompts/levantine.md | dialect (levantine, Arabic script) | native_authored |

Add a section below for every new variant (dialect, code-switched, Arabizi).

## Variant: levantine

- Author: the board (native Jordanian speaker)
- Reviewer: none yet (no second native speaker has reviewed this variant)
- Date: 2026-11-11
- Dialect / spelling notes: Jordanian (Levantine) dialect in Arabic script. Spelling and tashkeel (shadda on the yaa in the verb غيّر) are the author's choice and were copied byte-for-byte.
- Meaning matches the English prompt: yes (authored by the board)
- Issues found: none recorded

Checklist:

- [x] Wording is natural for a native speaker, not translationese
- [x] Same requirements as `prompts/en.md`: nothing added, nothing dropped
- [x] Code identifiers, file names and quoted Arabic strings match the fixture exactly
- [x] Diacritics and hamza spelling are intentional
- [x] File is UTF-8, no BOM, bidi control characters intact

## Variant: arabizi_levantine

- Author: the board (native Jordanian speaker)
- Reviewer: none yet (no second native speaker has reviewed this variant)
- Date: 2026-11-10
- Dialect / spelling notes: Levantine (Jordanian) Arabizi; `3'` stands for the letter غ; apostrophe is ASCII U+0027. Spelling is the author's choice.
- Meaning matches the English prompt: yes (authored by the board)
- Issues found: none recorded

Checklist:

- [x] Wording is natural for a native speaker, not translationese
- [x] Same requirements as `prompts/en.md`: nothing added, nothing dropped
- [x] Code identifiers, file names and quoted Arabic strings match the fixture exactly
- [n/a] Diacritics and hamza spelling are intentional
- [x] File is UTF-8, no BOM, bidi control characters intact

## Variant: en

- Author: the board (native Jordanian speaker)
- Reviewer: none yet (reference text)
- Date: 2026-11-10
- Meaning check: n/a (reference text)
- Issues found: none recorded

## Known grader limits

The AST checks in `tests/verify.py` are name-based and conservative. Contrived evasions are not chased:
- Module-level aliases of forbidden builtins (`s = sum` outside the function), or builtins fetched via `__import__` plus `getattr`.
- Recursion through `__globals__` or other indirect lookups; only direct calls by name, `globals()`, `locals()`, `eval` and `exec` are caught.
- A `while` placed after an early `return` is not treated as dead code.
- A BOM is reported as `no_bom` and `imports` together, because the decoded text fails to parse.

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
