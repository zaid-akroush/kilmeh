# Native-review record: arabic-search-normalize

**2026-11-21:** the `en` and `levantine` prompts are AI drafts that the board (native Jordanian speaker) approved unchanged in chat. Hashes are pinned in `tests/`. Per the process, the board sets `review_status` itself. Fixture Arabic still needs native review.

Task version: 0.1.1. Process: see `tasks/REVIEW_PROCESS.md`.

`review_status` in `task.toml` is set only by a native speaker, never by an agent. Nothing in this task has been reviewed by a native speaker yet.

## Variants

| Variant | File | Kind | review_status (task.toml) |
|---|---|---|---|
| en | prompts/en.md | en | draft (AI-written) |
| levantine | prompts/levantine.md | dialect (levantine, Arabic script) | draft (placeholder) |

## Variant: levantine

The file holds only `TODO(board): native Jordanian prompt, see REVIEW.md`. An agent never writes this prompt. The board writes it in Jordanian (Levantine) Arabic with the same requirements as `prompts/en.md` (all four normalization steps, what must stay untouched, the search and sort rules), then sets `review_status` and fills in the section below. `--strict` fails until then.

- Author: (board, native Jordanian speaker)
- Reviewer: none yet
- Date:
- Dialect / spelling notes:
- Meaning matches the English prompt:
- Issues found:

Checklist:

- [ ] Wording is natural for a native speaker, not translationese
- [ ] Same requirements as `prompts/en.md`: nothing added, nothing dropped
- [ ] Identifiers (`normalize_for_search`, `search`, `sort_names`, `casefold`) match the fixture exactly
- [ ] Code points (U+0600 to U+06FF, the seven Mn ranges, U+0640, U+0623, U+0625, U+0622, U+0671, U+0629, U+0649, U+0624, U+0626, U+0621, U+FDF2) are quoted exactly
- [ ] File is UTF-8, no BOM
- [ ] States the same rules `prompts/en.md` states: return the original record objects unchanged and in input order, never modify `records`, return the original strings from `sort_names`, no file writes at import, never write `/app` or read the grader

## Fixture content for native review

All of this was drafted by an agent and needs a native speaker. `fixture/contacts.py` (29 records) is the only fixed sample. The grader (`tests/verify.py`) does not reuse it: for every run it draws about 30 records, about 54 queries, the normalize inputs and the sort sets at random (`random.SystemRandom`), so a forged worker answer cannot be precomputed. Only the structure and these fixed Arabic items are written by hand: the words الله and the ligature U+FDF2, the letters ؤ ئ ء, the Persian letters پ چ ژ گ ک ی and ك, the variant letters أ إ آ ٱ ة ه ى ي, and the single-letter sort list. Invisible and combining characters are written with chr() in the grader and as `\u` escapes in the fixture; code points are listed below.

| Content | Where | Question for the board |
|---|---|---|
| Person names (records 1 to 22, 25 to 29, e.g. أحمد, إبراهيم, آمنة, فاطمة, مصطفى, موسى, يحيى, رؤوف, عائشة, لؤي, سمير, عبد الله) | contacts.py, verify.py | Are these natural, common Jordanian first and family names? Any that look odd or offensive? |
| City names (عمان, إربد, الزرقاء, العقبة, مادبا, السلط, الكرك, معان, عجلون, المفرق, الطفيلة, جرش) | contacts.py, verify.py | Spellings right? (Some are written deliberately without hamza, e.g. مادبا, or in a plain variant, e.g. عمان.) |
| Spelling variants on purpose: 2 احمد vs 1 أحمد; 7 فاطمه vs 6 فاطمة; 11 موسي vs 10 موسى (with tatweel); 13 مصطفي vs 12 مصطفى; 15 رؤوف vs 16 رءوف; 17 عائشة vs 18 عايشة; 19 لؤي vs 20 لوي; 28 سمير الأسعد vs 29 سمير الاسعد | contacts.py | Are these realistic variants that people type in a contact book? |
| Persian-letter record 27: `علی کریم` with U+06CC and U+06A9 | contacts.py, verify.py | Keep it? It exists to prove Persian letters are not folded to ي and ك. |
| Ligature record 21: `عبد ﷲ الناصر` with U+FDF2 | contacts.py, verify.py | Is U+FDF2 in a name realistic enough as a test of "do not expand ligatures"? |
| Latin and mixed records 23, 24, 25 (`Layla Haddad` / Amman, `LAYLA hamdan` / AQABA, سارة العلي / Irbid) and 30 (`Zaid Nimri`, grader only) | contacts.py, verify.py | none (Latin) |
| Marks used: U+0651 shadda (record 1, 28), U+064F damma and U+064E fatha (8, 28), U+0640 tatweel (10), U+0671 alef wasla (5), U+0654 hamza above in NFD form (26) | contacts.py | none (standard) |
| Normalize inputs (random letters from the pool ب ت ث ج ح خ د ذ ر ز س ش ص ض ط ظ ع غ ف ق ك ل م ن و, around the feature under test; all 13 Mn range endpoints, U+0640, U+0653 to U+0655, U+0624, U+0626, U+0621, U+FDF2, the folded letters, Latin with ß and e plus U+0301) | tests/verify.py | Are the words built from these letters a fair test? (They are random strings, not words.) |
| Hidden queries: random substrings of the random records, respelled with variant letters, tashkeel and tatweel; fixed items الله and U+FDF2; whole names and cities; Latin case swaps; negatives (random Latin and Arabic strings, empty, marks only, tatweel only, a Persian letter before a word) | tests/verify.py | Natural enough? Note a name or city that the grader draws is a random string, so any query is graded only by the specified rules. |
| Sort sets: seven per run, random words with ا أ إ آ ٱ ة ت prefixes, tashkeel and tatweel respellings, duplicates, mixed-case Latin, single letters ب أ ا ٱ ء ي ى ئ ة ه آ, an empty list, a one-element list | tests/verify.py | none beyond spelling |

## Notes and known grader limits

- The Mn ranges in the prompt were checked against Python 3.12's `unicodedata` (Unicode 15.0): U+0610 to U+061A, U+064B to U+065F, U+0670, U+06D6 to U+06DC, U+06DF to U+06E4, U+06E7 to U+06E8, U+06EA to U+06ED (52 code points). Same as the plan's rule. `tests/test_b_search.py::test_mn_ranges_match_python_unicodedata` pins this.
- Forged worker output: agent code shares the worker process and can write to the result channel (it inherits the duplicated stdout). The grader therefore draws every input at random per run, computes the expected results itself with its own normalizer, and checks record identity through ids the parent drew and a hash of the records it sent. Pinned by `test_constant_forge_replaying_a_previous_run_scores_0`, `test_inputs_are_random_but_keep_their_structure` and `test_worker_redirects_stdout_to_stderr_before_importing_the_agent`. Remaining limit: code in the worker could read the inputs from its own memory (for example the caller's frame) and compute answers from them. Closing that needs a worker that does not hold the inputs; it is left to a separate ticket.
- No top-level `def` check (0.1.1): 0.1.0 also required the three functions to be top-level `def`s in `search.py` (ast on the source). The prompt never states that rule, it scored correct solutions 0 (names bound by assignment such as `search = _search`, or re-exported with `from _impl import ...`), and it stopped nothing beyond the remaining limit above (a one-line stub `def` passes it). It is removed, with its `memory_forge` gaming case (a correct implementation written as lambdas). Pinned by `test_reference_bound_by_assignment_scores_1` and `test_reference_reexported_from_another_module_scores_1`.
- Readable `/app` (0.1.1): `tests/test.sh` runs `chmod -R a+rX /app` before locking `/tests`, as `arabic-digits-parse-format` does. Without it a correct solution saved with 0600 files or a 0700 `/app` scored 0, because the worker (uid 65534) could not read it. Pinned by `tests/test_b_search.py::test_in_image_0600_solution_scores_1` (docker).
- Parent/worker grader as in `arabic-digits-parse-format` (see `tasks/SCHEMA.md`, "Track B graders"): the agent's code runs only in `tests/worker.py`, as uid 65534 in its own session; `tests/verify.py` holds the expected values, locks `/tests` first and decides. Same remaining limit: a root `solve.sh` could tamper with `python3` before grading.
- The worker records, per search call, whether each returned record is the very input object and still equals a pristine copy, and whether the input list changed. `search_returns_originals` also requires input order.
- `sort_order_hidden` compares exactly when the returned strings are the inputs, and by normalized form when they are not, so a normalized-string return fails only `sort_returns_originals`.
- Alternative (b) in the plan ("NFD decomposition, filtering, then letter folding") cannot score 1 as written: NFD splits U+0624 and U+0626 into a plain letter plus U+0654, which is then stripped, so `no_over_normalization` fails. `tests/b_gaming/arabic-search-normalize/nfd_strip_all.py` pins that failure; the second passing alternative uses an explicit regex class, a `str.replace` chain and `cmp_to_key`.
- Not covered by this PR: `locale.strxfrm` gaming (needs the slim image: **verify** it fails) and the in-image reward/daemon cases (same code and image as `arabic-digits-parse-format`; `kilmeh selftest` runs this task's grader in the image).

## Sign-off

Reviewed by (name): ____________  Date: ____________  Result: approved / changes needed
