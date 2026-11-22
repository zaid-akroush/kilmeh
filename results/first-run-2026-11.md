# First agent run, November 2026: Codex CLI on a local 9B model

First local run. This is the Codex half. The Claude Code half came later, in the v1.0 run ([`v1-run-2026-11.md`](v1-run-2026-11.md)).

> **Read this first.** One small local model (9B parameters, 4-bit), 3 trials per variant. These numbers say nothing about frontier agents and are not a leaderboard entry. They show that the pipeline works end to end, and they give a first look at where a weak agent fails on Kilmeh's tasks.

## 1. Setup

| | |
|---|---|
| Agent | Codex CLI 0.167.2 |
| Model | Ollama `kilmeh-qwen3.5-9b-32k` = `qwen3.5:9b` Q4_K_M with `num_ctx` 32768 |
| Hardware | RTX 3070 8 GB; Ollama split the model 22% CPU / 78% GPU |
| Harness | Harbor 0.25.0, `-n 1` (one trial at a time), 3 attempts per variant, agent timeout 900 s |
| Tasks | 12 variants: 11 tasks in English, plus `loop-for-to-while` in Levantine and Levantine Arabizi. 36 trials. |
| When | Started 2026-11-14 00:26 local, finished 05:51 (about 5 h 25 min) |
| Tokens | 7.43 M input (7.18 M of them cached), 0.27 M output. No API cost (local model). |

An earlier attempt (`jobs-codex-ollama`) was killed by memory pressure after 1 trial. It is excluded from everything below.

A trial that hits the 900 s timeout is still graded: the verifier runs on whatever the workspace holds at the cut. So timeouts count as passes or fails, not as errors. That is why the `errors` column is 0 everywhere while Harbor itself reports 6 errored trials (all 6 are `AgentTimeoutError`).

## 2. Results (`kilmeh summarize-run`, verbatim)

| task variant | agent | trials | errors | passed | pass rate |
|---|---|---|---|---|---|
| arabic-bytes-survive-edit--en | codex/kilmeh-qwen3.5-9b-32k | 3 | 0 | 1 | 33% |
| arabic-digits-parse-format--en | codex/kilmeh-qwen3.5-9b-32k | 3 | 0 | 0 | 0% |
| arabic-in-code-farewell--en | codex/kilmeh-qwen3.5-9b-32k | 3 | 0 | 3 | 100% |
| arabic-search-normalize--en | codex/kilmeh-qwen3.5-9b-32k | 3 | 0 | 2 | 67% |
| loop-for-to-while--arabizi_levantine | codex/kilmeh-qwen3.5-9b-32k | 3 | 0 | 1 | 33% |
| loop-for-to-while--en | codex/kilmeh-qwen3.5-9b-32k | 3 | 0 | 2 | 67% |
| loop-for-to-while--levantine | codex/kilmeh-qwen3.5-9b-32k | 3 | 0 | 2 | 67% |
| rtl-contact-page-build--en | codex/kilmeh-qwen3.5-9b-32k | 3 | 0 | 0 | 0% |
| rtl-nav-fix--en | codex/kilmeh-qwen3.5-9b-32k | 3 | 0 | 0 | 0% |
| rtl-order-summary-fix--en | codex/kilmeh-qwen3.5-9b-32k | 3 | 0 | 0 | 0% |
| rtl-react-chat--en | codex/kilmeh-qwen3.5-9b-32k | 3 | 0 | 0 | 0% |
| rtl-tailwind-sidebar--en | codex/kilmeh-qwen3.5-9b-32k | 3 | 0 | 1 | 33% |

## loop-for-to-while: English vs Levantine vs Arabizi

| agent | en | levantine | arabizi_levantine |
|---|---|---|---|
| codex/kilmeh-qwen3.5-9b-32k | 2/3 | 2/3 | 1/3 |

## Parity vs English (pass rate / en pass rate)

| agent | task variant | parity |
|---|---|---|
| codex/kilmeh-qwen3.5-9b-32k | loop-for-to-while--arabizi_levantine | 0.50 |
| codex/kilmeh-qwen3.5-9b-32k | loop-for-to-while--levantine | 1.00 |

## Parity vs English per track (pooled)

| agent | track | parity |
|---|---|---|
| codex/kilmeh-qwen3.5-9b-32k | a-prompts | 0.75 |

Overall: 12 of 36 trials passed (33%). With 3 trials per variant, one trial moves a pass rate by 33 points, so the parity numbers above are noise-level.

## 3. Failure patterns per task

Counts are out of 3 trials. They come from each trial's `verifier/checks.json` or `verify.log` (failed checks), `result.json` (timeouts) and `agent/trajectory.json` (what the agent did). Checks not listed passed in all 3 trials.

### Track A: Arabic prompts (`loop-for-to-while`)

The fixture is one file, `/app/numbers.py`. The prompt doesn't name it.

| variant | passed | what the failures did |
|---|---|---|
| en | 2/3 | 1 trial asked the user for the code and stopped after one reply (16 s). It never ran `ls`. |
| levantine | 2/3 | 1 trial did the same, replying in Arabic and asking for the file name (14 s). |
| arabizi_levantine | 1/3 | 1 trial asked for the file name and stopped (26 s). 1 trial found `numbers.py`, then wrote a correct `while` version to a **new file**, `numbers_while.py`, and left `numbers.py` unchanged. |

- All 4 failures fail the same three checks: `has_while`, `no_for` and `while_reachable` (the graded file still has its `for` loop). Every other check passed.
- "Ask for the file and stop" happened in all three variants, English included. In this run it is a weak-model trait, not a dialect effect. The one failure unique to Arabizi is the new-file one.
- Reply language: the two failing Arabizi trials replied in a Latin-script language that is not Levantine Arabizi. It looks like Maltese (for example "jekk jogħġbok", Maltese for "please"); **verify** with the board. The passing Arabizi trial replied in Arabic script. The Levantine trials replied in Arabic script. Whether that is dialect or MSA is for native review, not this report.

### Track B: Arabic inside code

| task | passed | timeouts | failed checks |
|---|---|---|---|
| arabic-in-code-farewell | 3/3 | 0 | none (42 to 114 s) |
| arabic-search-normalize | 2/3 | 1 | `strips_tashkeel` 1/3, in the trial that timed out |
| arabic-bytes-survive-edit | 1/3 | 1 | `entry_inserted` 2/3, `untouched_lines_identical` 2/3, `csv_row_appended` 1/3 |
| arabic-digits-parse-format | 0/3 | 3 | see below |

- **bytes:** all the Arabic-specific byte checks passed in all 3 trials (bidi controls, ZWJ/ZWNJ, mark order, NFD line, NFKC-sensitive character, CRLF, no BOM, no final newline). The failures were about the edit itself: the new `strings.ts` entry wasn't inserted where asked and other lines changed. The trial that passed is the one that timed out (next section).
- **digits:** all 3 timed out, so the graded file is whatever `numerals.py` held at 900 s. Failed in 3/3: `parse_arab`, `parse_arabext`, `parse_decimal_sep`, `parse_grouping`, `format_arab`, `format_arabext`, `format_negative_and_rounding`, `roundtrip_seeded`, `caller_works`. Failed in 2/3: `parse_latn`, `format_latn`, `rejects_mixed_scripts`, `rejects_python_int_extras`, `rejects_bad_grouping`. Only `rejects_other_unicode_digits` passed in all 3.
- **digits, `ValueError`:** the grader calls `parse` on 47 inputs written in Arabic-Indic or Extended Arabic-Indic digits. These raised `ValueError` in 46, 23 and 22 of them in the three trials. Some of these inputs are ones the spec says to reject, so not every `ValueError` is wrong. In the 46/47 trial, single digits such as `parse("٠")` and `parse("٢")` raise. Its Western-digit parsing worked (`parse_latn` passed).

### Track C: right-to-left UI

| task | passed | failed checks |
|---|---|---|
| rtl-nav-fix | 0/3 | `on_side_signin` 3/3: sign-in centre at x = 779, 922 and 954 of 1280 (wanted on the left). `on_side_logo` 1/3. |
| rtl-order-summary-fix | 0/3 | `input_name_latin` 2/3, `bidi_isolated` 2/3, `svg_markup_unchanged` 2/3; `icon_next`, `icon_back`, `no_horizontal_overflow`, `table_fits` 1/3 each |
| rtl-react-chat | 0/3 | `input_composer_latin` 3/3, `bidi_isolated` 3/3, `bubbles_me_left` 2/3; `no_horizontal_overflow`, `card_fits` 1/3 each |
| rtl-contact-page-build | 0/3 | `icon_next`, `input_name_ar`, `svg_markup_unchanged`, `elements_fit_360` 3/3; `on_side_logo`, `no_physical_css`, `elements_fit_1280`, `readable_contrast_1280`, `readable_contrast_360` 2/3; `computed_direction`, `order_rtl_nav`, `no_horizontal_overflow_360` 1/3 |
| rtl-tailwind-sidebar | 1/3 | `main_beside_sidebar` 2/3: main's right edge at 1280 overlaps the sidebar, which starts at 1024. 1 timeout. The pass took 79 steps and 883 s. |

- **Latin text in an Arabic form field:** the field (order name, chat composer) inherits `direction: rtl` from the page, and Latin text typed into it stays right-to-left (`:dir(ltr)` false). That happened in 5 of 6 order/react trials. No react trial used `dir="auto"`. The one order trial that did use it passed `input_name_latin`, but it changed the back-icon SVG markup instead of flipping it with CSS.
- **Mixed-direction values not isolated** (`bidi_isolated`: an invoice number or product name with no `<bdi>` or `unicode-bidi: isolate`): 5 of 6 order/react trials.
- **Icons:** the agent edits SVG markup instead of mirroring it with CSS (`svg_markup_unchanged`) in 5 of 6 order/contact trials.
- **contact-page-build (built from scratch):** the model dropped required `data-testid`s (`page-header`, `contact-text`, `contact-form`, `nav-link`) in 2/3 trials. It also used grey text with contrast as low as 2.10:1 (2/3) and left the Arabic name field `direction: ltr` (3/3).

### Timeouts

6 of 36 trials hit 900 s: digits 3, bytes 1, search 1, tailwind 1. In all 6, the last trajectory step was a tool call, 2 to 87 s before the limit. The model was still working (debugging or re-checking), not sitting idle after a final answer. In one case (bytes, the trial that passed) the edits were already correct. The model was chasing a bug in its own check script: its script printed `ALL CHECKS PASS: False` for a CSV row that was in fact present. Two more trials finished just under the limit (react 860 s, tailwind 883 s). Track B tasks took this model 10 to 15 minutes even when it succeeded.

## 4. Excerpts

Trimmed, not otherwise edited. Arabic is copied byte-for-byte from `agent/trajectory.json`. Glosses are mine, one line, marked.

**a) Levantine prompt: asks for the file name and stops** (`loop-for-to-while--levantine`, trial `j3FD2QX`, 4 steps, no tool calls)

Prompt:

```text
بدي أزبط الفنكشن. غيّر من فر لوب لا وايل
```

Agent's final message:

```text
أهلاً! أريد مساعدتك في تحويل loop من `for` إلى `while`. لكني أحتاج إلى بعض المعلومات أولاً:

1. ما هو **اسم الملف** الذي يحتوي على الدالة؟
2. أو هل تريد أن أرأيه؟
```

*Gloss: "Hello! I want to help you convert the loop from for to while, but I need some information first: 1. What is the file name that contains the function? 2. Or do you want me to see it?"*

**b) Arabizi prompt: right change, wrong file** (`loop-for-to-while--arabizi_levantine`, trial `peLCnBp`)

Prompt:

```text
biddi azabit il function. 3'ayerha min for loop la while.
```

After `ls -la` and `cat numbers.py`, the agent's tool call (trimmed after the function):

```bash
cat > numbers_while.py << 'EOF'
def sum_positive(numbers):
    total = 0
    index = 0
    while index < len(numbers):
        n = numbers[index]
        if n > 0:
            total += n
        index += 1
    return total
```

The first line of its final message, and a sibling trial's (`WTZoXjQ`) whole reply:

```text
Hawnha l-convertion min `for` loop el-while loop:
```

```text
Ah, t'ghedti trid tiħallihom tbiddil funzjoni? Jien infurza li ma naraxx l-kodċi jew il-fajl fejn hija f'din il-funzjoni b'for loop.

Jekk għandek il-kodiċi, jekk jogħġbok:
1. Ħallihom ikkomputa dan il-fajl
2. Ikkopja u ħalla l-for loop hemm
3. Nibdlu bil-while loop

Tistgħu tgħidilni x'isem il-fajl?
```

*Gloss: not Levantine Arabizi; it looks like Maltese (**verify**). The reply asks which file holds the function.*

**c) Digits: Extended Arabic-Indic grouping and decimal separators** (`arabic-digits-parse-format--en`, trial `Ad6RFiD`, step 10, tool output)

```text
String: '۱٬۲۳۴٫۵'
Result: 15
Expected: 1234.5
Match: False
```

It rewrote `numerals.py` and got `ValueError: Latin comma not allowed in Arabic digit system` on the same input. Then the 900 s limit hit.

## 5. What this does and doesn't show

**Does show**
- The full pipeline works on Windows with Docker: export to Harbor, 36 trials, verifier, `summarize-run` with its secret scan. No infra errors.
- The graders separate trials by behaviour. Every failure above maps to a named check with a reason in the log, except where the logging ticket below applies.
- The RTL failures are the ones Kilmeh was built to catch: Latin input in RTL fields, missing bidi isolation, mirrored icons, physical sides.

**Doesn't show**
- Anything about frontier agents or about Codex with its intended models.
- A dialect or Arabizi penalty. The track A gap (2/3, 2/3, 1/3) is one trial wide, and the main failure mode also hit English.
- Arabic-prompt results for tracks B and C. Those tasks have no native-written Arabic prompts yet.

**Tickets found**
1. **Grader logging**. `verify.log` is inconsistent across tasks. RTL tasks print a `PASS`/`FAIL` line per check. `loop-for-to-while` and `arabic-in-code-farewell` print the check dict. `arabic-digits-parse-format` and `arabic-search-normalize` print only the worker calls and results. `arabic-bytes-survive-edit` leaves it empty. The verdicts for those three are only in `checks.json`. A per-check `PASS`/`FAIL` summary in `verify.log` changes the grader, so it needs new task versions and a changelog entry.
2. **Timeout budget.** With this model, 900 s cuts off Track B work in progress (digits 3/3). It also cut off one trial that had finished and was over-verifying. Both are model behaviour, not grader bugs. Decide whether to keep 900 s for the Claude Code half, so the two halves are comparable.
3. **`summarize-run` and timeouts** (small). Graded timeouts show as plain fails with `errors` 0. A timeouts column would make that visible without reading Harbor's `result.json`.
