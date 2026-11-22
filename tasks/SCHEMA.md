# Kilmeh task schema (v1)

Source of truth for task structure. Graders and the runner code against this; a later converter compiles it to Harbor task folders. The validator (`src/kilmeh/tasks/`) enforces the rules below. It checks structure only: it never runs Docker or the solutions.

```
uv run kilmeh validate-tasks [PATHS...] [--strict]   # default path: tasks/
```

Exit code is non-zero on any error; each error names the file and field.

## Layout

```
tasks/<track>/<task-id>/
  task.toml                 metadata (read with stdlib tomllib)
  prompts/<variant>.md      one UTF-8 file per prompt variant, no BOM
  fixture/                  repo snapshot the agent starts from
  environment/Dockerfile
  tests/                    grader entry (test.sh, pytest files, ...)
  solutions/reference/      must pass the grader
  solutions/known-bad/      must fail the grader
```

Held-out tasks live only in `tasks/heldout/` (git-ignored), never in the public tree.

## Fields

| Field | Rule |
|---|---|
| `schema_version` | `"1"` |
| `id` | kebab-case, equals the directory name |
| `version` | semver (`0.1.0`) |
| `track` | `a-prompts`, `b-arabic-in-code`, `c-rtl-ui`, `d-output-language` |
| `title` | non-empty string |
| `difficulty` | `easy`, `medium`, `hard` |
| `split` | `public` or `heldout` |
| `pair_id` | optional string; groups prompt variants of the same underlying task |
| `stack` | optional list of free strings (framework, language) |
| `[prompts.<variant>]` | `file`, `lang` (`en`/`ar`), `kind` (`en`/`msa`/`dialect`/`code-switched`), `script` (`arabic` default, or `latin` for Arabizi; `latin` requires `lang = "ar"`), `dialect` (iff `kind = "dialect"`: `levantine`, `gulf`, `egyptian`, `maghrebi`, `iraqi`, `sudanese`, `other`), `review_status` (`draft`/`native_authored`/`native_reviewed`) |
| `[grader]` | `type` (`tests`/`arabic-integrity`/`rtl`/`language-id`), `entry` (required, a file inside `tests/`), `timeout_seconds` (> 0) |
| `[solutions]` | `reference` and `known_bad`: directories in the task dir |

Unknown fields are rejected. Paths are relative to the task directory and must stay inside it.

## Validator rules

1. Every required field is present and valid.
2. `track` is one of the four listed tracks.
3. `id` equals the directory name.
4. `version` is semver.
5. At least one prompt variant has `lang = "en"`.
6. At least one prompt variant has `lang = "ar"` and `script = "arabic"` (Arabizi alone does not count).
7. `kind = "dialect"` requires `dialect` (and `dialect` is rejected for other kinds).
8. Any prompt with `review_status = "draft"` is allowed normally and rejected under `--strict` (used for releases).
9. Referenced prompt files and `grader.entry` exist (`grader.entry` must be a file). Paths are resolved through symlinks and must stay inside the task directory.
10. Prompt files are valid UTF-8, do not start with a BOM, are not empty or whitespace-only, and contain no NUL. Two variants must not point at the same file. `task.toml` itself must be valid UTF-8 TOML.
11. `solutions/reference` and `solutions/known-bad` directories exist, and are not the task root.
12. `reference` and `known_bad` resolve to different, non-nested directories.
13. `split = "heldout"` is rejected unless the task sits directly under the nearest `tasks/heldout/` ancestor (resolved path; a parent folder merely named `heldout` does not count).
14. `fixture/`, `tests/` and `environment/Dockerfile` exist.
15. `lang`/`kind` agree: `kind = "en"` needs `lang = "en"`; `msa`, `dialect` and `code-switched` need `lang = "ar"`.
16. `title`, `pair_id` (if set), `grader.entry` and path fields are not blank.
17. `script` is `arabic` or `latin`, and `latin` requires `lang = "ar"`.
18. Both solution directories contain `solve.sh`.
19. `grader.entry` is spelled under `tests/` and resolves (through symlinks) to a file inside the task's `tests/` directory.
20. Every `COPY` or `ADD` in `environment/Dockerfile` (any case, flags such as `--chown` ignored, JSON-array form and backslash continuations handled) has only sources that are `fixture` or start with `fixture/`, with no `..`. `COPY --from=<stage>` is exempt; quoted sources are unquoted first. A `RUN --mount` of type `bind` (the default type) without `from=` is rejected, because it can reach `tests/` or `solutions/` in the build context; cache, tmpfs, secret and ssh mounts are allowed. The error names the line.

The loader never normalizes or rewrites prompt text; Arabic stays byte-for-byte as written.

## Run contract

Every tool that runs a task (our self-test, Harbor, a future runner) follows these rules.

1. **Image.** Built from `environment/Dockerfile`. The Dockerfile copies only from `fixture/` and puts the starting files in `/app`, the workspace.
2. **Solution.** A solution directory is made available at `/solution`. It is applied with `bash /solution/solve.sh`, working directory `/app`. `/tests` does not exist yet while it runs.
3. **Grader.** After the solution step, `tests/` is copied into the same container as a writable `/tests` (never a bind mount), the way Harbor copies it in with its Docker environment (Harbor 0.25.0: `verifier/verifier.py` calls `environment.upload_dir(tests, /tests)`, and `environments/docker/docker_unix.py` runs `docker compose cp <tests>/. main:/tests`; **verify** for non-Docker environments). A grader may lock it down (for example `chown -R 0:0 /tests; chmod -R go-rwx /tests`). The self-test does this by starting the container twice: the first start applies the solution, then the host runs `docker cp tests/. <container>:/tests`, and the second start runs the grader. If the solution created `/tests` itself, the run is refused (no reward). The grader is run with `bash /tests/<entry file>`. It writes `1` (pass) or `0` (fail) to `/logs/verifier/reward.txt`. Its exit code is ignored. The file must hold exactly `1` or `0`, optionally followed by a single LF (what `echo 1 >` writes). A missing file or any other content (spaces, CRLF, extra lines) is a fail. The host reads the file after the container stops, with `docker cp` (never from the container's output), and accepts only a single regular file, not a link, of at most two bytes. The network is off.
4. **Self-test.** `uv run kilmeh selftest` must show: reference = 1, known-bad = 0, and the untouched fixture = 0. A task whose starting state already passes is broken.

```
uv run kilmeh selftest [PATHS...]   # default path: tasks/. Needs Docker.
```

Exit code 0 if every task is proven, 1 if any task is not, 2 if a task is invalid or Docker is unavailable.

## Harbor export

```
uv run kilmeh export-harbor OUT_DIR [PATHS...]   # default path: tasks/
```

Writes one Harbor task folder per prompt variant, `OUT_DIR/<id>--<variant>/`, and prints each path. A folder holds `instruction.md` (the prompt file's bytes), `task.toml` (Harbor schema 1.4, with our metadata), `environment/` (the Dockerfile and a copy of `fixture/`), `tests/` and `solution/` (the reference solution). The known-bad solution is never exported. Held-out tasks are refused. Invalid tasks exit 1 and nothing is written. An existing variant folder is replaced, so no stale file survives. The grader entry must be `tests/test.sh`. A prompt file whose bytes start with `TODO(board)` is a placeholder for a prompt the board has not written yet: that variant is skipped and no folder is written for it. A non-English prompt (`lang = "ar"`, Arabizi included) with `review_status = "draft"` is skipped the same way: `draft` means AI-written or unreviewed (`tasks/REVIEW_PROCESS.md`), so only `native_authored` and `native_reviewed` Arabic variants are exported. English prompts are exported whatever their `review_status`. Harbor is not a dependency; our schema stays the source of truth.

## Example

A runnable copy lives in `tests/fixtures/tasks/valid/arabic-in-code-farewell/`.

```toml
schema_version = "1"
id = "arabic-in-code-farewell"
version = "0.1.0"
track = "b-arabic-in-code"
title = "Add a function without altering Arabic bytes"
difficulty = "easy"
split = "public"
pair_id = "arabic-in-code-farewell"
stack = ["python"]

# The MSA prompt is AI-written: it needs native-speaker review before release.
[prompts.en]
file = "prompts/en.md"
lang = "en"
kind = "en"
review_status = "draft"

[prompts.msa]
file = "prompts/msa.md"
lang = "ar"
kind = "msa"
review_status = "draft"

# Arabizi variant: Arabic in Latin letters and digits. Several spellings per task are
# allowed (arabizi_egy_a, arabizi_egy_b, ...), sharing the same pair_id.
[prompts.arabizi_egy_a]
file = "prompts/arabizi_egy_a.md"
lang = "ar"
kind = "dialect"
dialect = "egyptian"
script = "latin"
review_status = "native_authored"

[grader]
type = "arabic-integrity"
entry = "tests/test.sh"
timeout_seconds = 120

[solutions]
reference = "solutions/reference"
known_bad = "solutions/known-bad"
```

The example above adds an Arabizi variant that the on-disk fixture omits. The on-disk sample's prompts are AI drafts, so it fails `--strict` with one error per prompt. Set every prompt to `native_authored` or `native_reviewed` to pass (covered in `tests/test_task_validator.py`).

## RTL grader (`type = "rtl"`)

Tasks in track `c-rtl-ui` grade a web page with a browser and no model: headless Chromium reads the DOM, computed styles and `getBoundingClientRect`. The canonical check library is `src/kilmeh/graders/rtl_checks.py` (standard library plus the Playwright sync API).

**Four grader files per task**, in `tests/`:

- `build.sh APP OUT`: rebuilds generated output (Tailwind, React) from the agent's source into `OUT`; a no-op for plain HTML. The grader never trusts an agent-edited `dist/`.
- `verify.py APP OUT`: serves the page from disk through Playwright routing (no port; every request outside the local origin is aborted and WebSockets are mocked, so nothing reaches the network), runs the task's list of checks and prints one boolean per check as JSON. It exits 0 only if all pass.
- `test.sh`: byte-identical in every RTL task. It writes `0` first, then `1` only if build and verify both succeed, so a crash never leaves a stale `1`.
- `rtl_checks.py`: a byte-identical vendored copy of the canonical library, so each task folder is self-contained for Harbor. `tests/test_rtl_vendoring.py` fails on any drift (`cp src/kilmeh/graders/rtl_checks.py <task>/tests/`).

**Base image.** Every RTL `environment/Dockerfile` ends in the same pinned Playwright Python image (tag and digest) and installs the Python bindings with `pip --require-hashes --no-deps` from hashes copied from `uv.lock`. A repo test keeps the image, the `playwright` pin and the hashes in step.

**Checks** (each has a known-good and a known-bad test in `tests/test_rtl_checks.py`): `root_dir_lang`, `computed_direction`, `no_horizontal_overflow` (scroll width plus a visible-element geometry pass), `fits_width`, `on_side`, `order_rtl`, `mirror_on_dir_flip` (flips only `<html dir>`; graded elements must be asymmetric), `no_physical_css` (static sheets, `@import`, adopted sheets, open shadow roots, inline styles, plus a computed-style pass), `no_physical_tailwind`, `icon_points`, `bidi_isolated`, `input_direction`, `visual_order` (known tokens, found in typed order in an element's text, read left to right or right to left on screen; hidden, covered, mirrored or flipped, wrapped or letter-reversed tokens fail; needs 2+ tokens), `text_kept` (graded `data-testid` text equals the fixture's, ignoring only invisible direction marks U+2066-2069, U+200E, U+200F and all whitespace; expected text from `testid_texts` on a byte copy of the fixture). Tasks add task-local checks in `verify.py` where the library has none.

**Per-task tests** (`tests/test_rtl_tasks.py`, marker `docker`): the reference passes, the known-bad and the untouched fixture fail an exact, pinned set of checks, every check fails alone under its own mutation (`tests/rtl_mutations/<task>/<check>.py`), `verify.py` exits non-zero whenever a check fails, correct alternative solutions with other techniques score 1 (`tests/rtl_alternatives/`), and gaming attempts such as clipping, shrinking, hiding or planting grader files score 0 (`tests/rtl_gaming/`).

**Prompts.** Prompts are short requests, like a real developer would write. The full graded requirements, including task-local rules (for example the contact page's definition of "visible", its exact element counts, its visible-Arabic and static-page rules), are in `fixture/SPEC.md` (English, identical for every variant), so the agent finds them in its workspace. In the Tailwind tasks `fixture/.gitignore` lists `SPEC.md` so Tailwind does not compile class names mentioned there. The Jordanian variant `levantine.md` is board-approved and hash-pinned in `tests/test_rtl_vendoring.py`. Every Arabic string in fixtures and solutions is listed in the task's `REVIEW.md` under "Fixture content for native review".

## Track B graders (agent code under test)

A Track B task whose grader runs the agent's code splits it into a **parent** and a **worker**, so the agent's process can never decide the exit code or the reward. The pattern is set by `tasks/b-arabic-in-code/arabic-digits-parse-format/`; later tasks copy it.

- **Parent** (`tests/verify.py`, run as `python3 -I -S`): holds every input and expected value and never imports from `/app`. It starts the worker with a timeout, compares the worker's raw outputs in its own process (strings and exact `Decimal` values, never the agent's objects), prints one boolean per check as JSON and exits 0 only if all pass.
- **Worker** (`tests/worker.py`, started as `python3 -I -S -c <source>` because it cannot read `/tests`): reads the calls from stdin, imports the stdlib first, appends `/app` to the **end** of `sys.path` (a planted `/app/json.py` cannot shadow the stdlib), points fd 1 at stderr while agent code runs (the parent discards stderr), and writes one JSON list of raw results to its saved stdout. It decides nothing: `os._exit(0)`, fake JSON or a crash all leave the parent with no well-formed answer, so every check fails.
- **Locked grader, fail closed:** `test.sh` runs `chown -R 0:0 /tests` and `chmod -R go-rwx /tests` before verify, so uid 65534 cannot read the expected values. Before any agent code runs, verify walks its own `tests/` directory and refuses to grade (exit 2, reason on stderr, reward 0) unless every entry is owned by the grading user (root in the container) with no group or other permission bits. A runner that bind-mounts `/tests` read-only, or leaves it world-readable, therefore scores every solution 0 instead of silently reopening the hole.
- **Isolation:** when the parent is root, the worker runs as uid/gid 65534 with no supplementary groups (`user=`, `group=`, `extra_groups=[]`) and `start_new_session=True`. Afterwards the parent kills the worker's process group, then runs `kill(-1, SIGKILL)` as uid 65534, three times, which also kills daemons that left the session. Verified in the pinned image under `kilmeh selftest` and under Harbor 0.25.0 (both run the grader as root). **When the parent is not root** (host repo tests), there is no uid drop and only the process group is killed.
- **Hidden supersets:** `tests/` is mounted only at grade time, so the graded inputs are a strict superset of the examples in `fixture/`. Seeded inputs use a constant seed in the parent; there is no clock, locale or ICU dependency.
- **`test.sh` order:** (1) `mkdir -p /logs/verifier`, `rm -f` and `echo 0 >` the reward file; (2) lock `/tests`; (3) run verify; (4) write `1` or `0` in **both** branches, so a reward planted at agent time never survives.
- **Repo tests** (`tests/test_b_<short>.py`, helpers in `tests/b_helpers.py`): sha256 pins for the fixture and prompts, the `FROM` line pinned by tag and digest, exact failing-check sets for the reference (none), known-bad and untouched fixture, one isolation mutation per check (`tests/b_mutations/<id>/<check>.py`), two independent alternatives that score 1 (`tests/b_alternatives/<id>/`) gaming cases that score 0 (`tests/b_gaming/<id>/`), and probes on top of the reference that pin each worker guard (`tests/b_probes/<id>/`: exact `Decimal` and `str` types, app directory last on `sys.path`, agent stdout discarded). A host test runs verify on a world-readable copy of `tests/` and expects the refusal. Cases that need the container (uid drop, locked `/tests`, planted reward, forked daemon, reading the grader) carry the `docker` marker.
- **Limit:** grading still happens in the solution's own container. A root `solve.sh` can tamper with the tools the grader uses (`python3`, `bash`, the stdlib) before `/tests` arrives; only a separate, clean grading container closes that (see Known limits). On a runner where the grader is not root there is no uid drop, so the worker could read the grader: such a runner is not supported for Track B.

## Text-integrity grader

`kilmeh.graders.text_integrity.check(original: bytes, edited: bytes) -> list[Result]` (standard library only) reports what an edit broke. Each `Result` is `(key, passed, detail)` and prints as `PASS key: detail`. It never normalizes or reorders its inputs. "Arabic text" means the Arabic-script characters (Arabic blocks and presentation forms, minus U+061C), in order; everything else may change freely.

- `valid_utf8`: the edited file decodes as UTF-8.
- `no_bom_added`: the edited file has no UTF-8 BOM the original lacked.
- `byte_exact`: the Arabic characters are identical, in order. A changed code point, including NFC/NFD drift, fails this too.
- `normalization_unchanged`: the Arabic text keeps its NFC, NFD and NFKC status.
- `bidi_controls_kept`: U+200E, U+200F, U+061C, U+202A-202E and U+2066-2069 have the same sequence.
- `joiners_kept`: ZWJ U+200D and ZWNJ U+200C have the same sequence.
- `no_mojibake`: no new U+FFFD and no new cp1252/latin-1 double-encoding pattern (`Ø`/`Ù`/`Ú`/`Û` plus a continuation byte).

Limits: sequences are checked, positions are not (moved Arabic, bidi controls or joiners pass). Line endings are not checked (CRLF passes). `no_mojibake` is a heuristic: "Ø" followed by U+0080-00BF can false-fail.

Not covered: tashkeel and tatweel have no check of their own, because removing one already fails `byte_exact`.

## Language-ID grader

`kilmeh.graders.lang_id` (standard library only) checks that an agent answers and comments in the language it was asked in. `detect(text)` returns `"ar"`, `"en"`, `"mixed"` or `"none"` from the share of Arabic words among Arabic plus Latin words (a word is Arabic when most of its letters are): at least 0.5 is `ar`, at most 0.2 is `en`, between is `mixed`. `check` raises `ValueError` unless `expected` is `ar` or `en`; failures have their own "not in the expected language" detail. Fenced code, `` `inline code` ``, URLs and identifier-like tokens (snake_case, camelCase, `a.b`, `f()`) are ignored first; digits and punctuation are never letters. `comments(source, lang)` returns comment texts from Python (`tokenize`) or JS/TS (`//`, `/* */`).

`check(text, expected="ar", *, source=None, lang="py") -> list[Result]` gives `response_language`, and `comments_language` when `source` is given. A result passes only when the detected label equals `expected`. Empty or letterless input (including Arabic-Indic digits only) and source with no comments detect as `none` and fail with the detail "no letters to classify".

Limits: Arabizi is not detected and counts as English. English words outside backticks count as English. Short texts swing the ratio. Other Arabic-script languages count as `ar`. Commit messages go through `response_language` as plain text.

## Known limits

Not checked yet: that Arabic-language prompts actually contain Arabic script, that `id` is unique across tasks, maximum lengths and timeouts, whether the reference and known-bad solutions differ in content (the grader self-test covers that), and an upper bound on `timeout_seconds` (deferred).

Container memory and process limits are not set by the self-test yet.

Duplicate task ids across the tree are not detected yet.

Arabizi has no standard spelling: spelling conventions are the author's choice, and Arabizi prompts need native authoring or review. Language-id tools tend to label Arabizi as English, so Track D will need a custom check later.

In-container grading can be defeated by a solution that tampers with the container's own tools (for example replacing `python3`), because the grader runs in the same container as the solution. A stronger setup would run the grader in a separate, clean container.

RTL grader limits: the grader trusts the in-container Chromium, Python and Node (and Tailwind), the same tampering limit as above. The mirror check flips only `<html dir>` and is vacuous for boxes symmetric about the page centre. Physical CSS in closed shadow roots is not seen, and `dir` or `lang` set by JavaScript at load time is accepted. `zoom` and `transform` scale are checked per task, not in the library, and a rule's `allow` list matches selector text exactly. `@keyframes` and `background-position` are not graded. `visual_order` limits: an overlay with `pointer-events: none` is skipped by its hit test (`elementFromPoint`), as is a `::before`/`::after` overlay of the graded element itself; paint-only hiding (`color: transparent`, text the same colour as the background, `filter: opacity()`) is not detected; overlapping glyphs from `letter-spacing`, and text changed only on screen by `text-transform` or `::before`/`::after` `content`, are not detected; and tokens wrapped onto another line on a narrow layout fail even when the order is right. The Arabic prompts are placeholders until the board writes them.
