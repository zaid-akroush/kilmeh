"""Grader tests for arabic-bytes-survive-edit (Track B, byte-integrity grader).

This grader never runs agent code: it reads three files' bytes and compares them with the
golden originals. Host tests run tests/verify.py against a temp copy of the fixture
(KILMEH_APP). Each check fails under its own mutation (tests/b_mutations/); the preservation
checks fail together with `untouched_lines_identical`, and those sets are pinned exactly. Two
independent correct alternatives score 1 (tests/b_alternatives/), gaming scores 0
(tests/b_gaming/). The container cases (locked /tests, planted reward, a uid-65534 daemon, real
sed and printf) carry the `docker` marker: `uv run pytest -m docker tests/test_b_bytes.py`.
"""

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import unicodedata

import pytest

from b_helpers import (
    ROOT,
    apply,
    check_lines,
    failing,
    fresh_app,
    run_in_image,
    run_verify,
    run_verify_raw,
    task_dir,
)
from kilmeh import selftest

TASK_ID = "arabic-bytes-survive-edit"
TASK = task_dir(TASK_ID)
MUTATIONS = ROOT / "tests" / "b_mutations" / TASK_ID
ALTERNATIVES = ROOT / "tests" / "b_alternatives" / TASK_ID
GAMING_DIR = ROOT / "tests" / "b_gaming" / TASK_ID
GENERATOR = ROOT / "tests" / "b_fixture_gen" / f"{TASK_ID}.py"

CHECKS = {
    "version_bumped",
    "entry_inserted",
    "csv_row_appended",
    "untouched_lines_identical",
    "bidi_controls_preserved",
    "zwj_zwnj_preserved",
    "mark_order_preserved",
    "nfd_line_preserved",
    "nfkc_char_kept",
    "no_final_newline_added",
    "crlf_preserved",
    "no_bom",
    "valid_utf8",
    "readme_unchanged",
}

FIXTURE_SHA256 = {
    "src/strings.ts": "6ebb82de6374c7eafe2920b60051e5245dcad45c2ef8dc4192a30a962f7e35ea",
    "locale/ar.csv": "1bd1e1afb0e4c6bf5db7b14b8688e3f716ff157cb57e95e9335048102db0cecd",
    "README.md": "30b914fbba4ca7e0c15fc1947e8cdc55db863b5f55c4c5ffef8f504e893cd3a5",
    "SPEC.md": "cc6e848e2f9f827d20fbce9b502aeb2d8ca01b92445ae4fabe48a7a10ebe6692",
}
PROMPT_SHA256 = {
    "en.md": "4e946455d59f7738f5c2fc6472f30e3bee9499c7cfeb0774c83a8ef9ceddff0a",
    "levantine.md": "7976552212cfe6e00bb51297613ef7ddb2e4effb83f46ca9c9d03a7e2f2c98f6",
}
FROM_LINE = (
    "FROM python:3.12.15-slim-bookworm"
    "@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70"
)

# Observed with the reference grader; exact, so a new false pass or fail is noticed.
KNOWN_BAD_FAILS = {"crlf_preserved", "untouched_lines_identical"}
UNTOUCHED_FAILS = {"version_bumped", "entry_inserted", "csv_row_appended"}

# Mutation (on top of the reference) -> exact failing set. Preservation checks fail together
# with untouched_lines_identical; the three edit checks and readme_unchanged fail alone.
U = "untouched_lines_identical"
MUTATION_FAILS = {
    "version_bumped": {"version_bumped"},
    "entry_inserted": {"entry_inserted"},
    "csv_row_appended": {"csv_row_appended"},
    "untouched_lines_identical": {U},
    "bidi_controls_preserved": {"bidi_controls_preserved", U},
    "zwj_zwnj_preserved": {"zwj_zwnj_preserved", U},
    "mark_order_preserved": {"mark_order_preserved", U},
    "nfd_line_preserved": {"nfd_line_preserved", U},
    "nfkc_char_kept": {"nfkc_char_kept", U},
    "no_final_newline_added": {"no_final_newline_added", U},
    "crlf_preserved": {"crlf_preserved", U},
    "no_bom": {"no_bom", U},
    "valid_utf8": {"valid_utf8", U},
    "readme_unchanged": {"readme_unchanged"},
}

# Gaming case -> (runs on top of the reference, exact failing set).
GAMING = {
    "os_exit_at_import": (False, UNTOUCHED_FAILS),
    "constant_forge": (False, UNTOUCHED_FAILS),
    "copy_golden": (False, UNTOUCHED_FAILS),
    "symlink_file_out": (True, CHECKS),
    "symlink_dir_out": (True, CHECKS),
    "nfc_everything": (True, {"mark_order_preserved", "nfd_line_preserved", U}),
    "nfkc_everything": (
        True,
        {"mark_order_preserved", "nfd_line_preserved", "nfkc_char_kept", U},
    ),
    "strip_invisible": (True, {"bidi_controls_preserved", "zwj_zwnj_preserved", U}),
    "dos2unix_everything": (True, {"crlf_preserved", U}),
    "unix2dos_everything": (
        True,
        {
            "crlf_preserved",
            "entry_inserted",
            "mark_order_preserved",
            "nfd_line_preserved",
            "nfkc_char_kept",
            "readme_unchanged",
            "version_bumped",
            U,
        },
    ),
    "formatter_rewrite": (True, {"no_final_newline_added", U}),
    "entry_at_wrong_spot": (True, {"entry_inserted", U}),
    "rewrite_from_visible_text": (
        True,
        {
            "bidi_controls_preserved",
            "zwj_zwnj_preserved",
            "mark_order_preserved",
            "nfd_line_preserved",
            "nfkc_char_kept",
            "no_final_newline_added",
            U,
        },
    ),
}

# Characters the fixture must contain (each is graded by a check above).
FIXTURE_CODE_POINTS = {
    0x200E, 0x200F, 0x061C, 0x202A, 0x202B, 0x202C, 0x2066, 0x2067, 0x2068, 0x2069,  # bidi
    0x200C, 0x200D, 0x1F468, 0x1F469, 0x1F467,  # joiners and the family emoji
    0x0651, 0x064E, 0x0653, 0xFDF2, 0x00A0,  # marks, NFD pair, ligature, nbsp
}  # fmt: skip


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def app(tmp_path):
    return fresh_app(TASK, tmp_path)


def fixture_files():
    root = TASK / "fixture"
    return {p.relative_to(root).as_posix(): p for p in root.rglob("*") if p.is_file()}


def test_fixture_files_are_pinned():
    files = fixture_files()
    assert set(files) == set(FIXTURE_SHA256)
    for name, expected in FIXTURE_SHA256.items():
        assert sha256(files[name].read_bytes()) == expected, name


def test_prompts_are_pinned():
    for name, expected in PROMPT_SHA256.items():
        assert sha256((TASK / "prompts" / name).read_bytes()) == expected, name


def test_dockerfile_copies_only_the_fixture_and_pins_the_image():
    """tests/golden is not in the image at agent time: only fixture/ is copied in."""
    lines = (TASK / "environment" / "Dockerfile").read_text("utf-8").splitlines()
    assert lines == [FROM_LINE, "WORKDIR /app", "COPY fixture/ /app/"]
    assert re.fullmatch(r"FROM python:3\.12\.\d+-slim-bookworm@sha256:[0-9a-f]{64}", lines[0])


def test_generator_reproduces_fixture_and_golden_bytes(tmp_path):
    subprocess.run([sys.executable, "-I", str(GENERATOR), str(tmp_path)], check=True)
    made = {
        p.relative_to(tmp_path).as_posix(): p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file()
    }
    assert set(made) == set(FIXTURE_SHA256) - {"SPEC.md"}
    for name, data in made.items():
        assert fixture_files()[name].read_bytes() == data, name
        assert (TASK / "tests" / "golden" / name).read_bytes() == data, name


def test_golden_holds_exactly_the_fixture_files():
    root = TASK / "tests" / "golden"
    assert {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} == set(
        FIXTURE_SHA256
    ) - {"SPEC.md"}


def test_fixture_has_the_deliberate_traps():
    ts = (TASK / "fixture" / "src" / "strings.ts").read_bytes()
    csv = (TASK / "fixture" / "locale" / "ar.csv").read_bytes()
    assert not ts.endswith(b"\n") and b"\r" not in ts
    assert csv.endswith(b"\r\n") and csv.count(b"\n") == csv.count(b"\r\n")
    assert b",   \n" in ts, "a line with trailing spaces"
    for data in (ts, csv, (TASK / "fixture" / "README.md").read_bytes()):
        assert not data.startswith(b"\xef\xbb\xbf")
        data.decode("utf-8")
    text = ts.decode("utf-8")
    assert {ord(c) for c in text if ord(c) > 0x7F} >= FIXTURE_CODE_POINTS
    # shadda before fatha: NFC would reorder it; alef + U+0653: NFC would compose it
    assert unicodedata.normalize("NFC", text) != text
    assert unicodedata.normalize("NFKC", text) != unicodedata.normalize("NFC", text)
    assert chr(0x651) + chr(0x64E) in text and chr(0x627) + chr(0x653) in text


def test_text_files_outside_the_fixture_are_utf8_without_bom_or_crlf():
    for path in TASK.rglob("*"):
        if path.is_file() and "golden" not in path.parts and "fixture" not in path.parts:
            data = path.read_bytes()
            assert not data.startswith(b"\xef\xbb\xbf"), path
            assert b"\r" not in data, path
            data.decode("utf-8")


def test_invisible_characters_are_escapes_in_sources():
    """No literal Mn, Cf or Lm character in the grader, solutions, QA scripts or generator."""
    paths = [
        TASK / "tests" / "verify.py",
        GENERATOR,
        *(TASK / "solutions").rglob("*.py"),
        *MUTATIONS.glob("*.py"),
        *ALTERNATIVES.glob("*.py"),
        *GAMING_DIR.glob("*.py"),
    ]
    for path in paths:
        for ch in path.read_text("utf-8"):
            assert unicodedata.category(ch) not in ("Mn", "Cf", "Lm"), (path, hex(ord(ch)))


def _verify_constants():
    tree = ast.parse((TASK / "tests" / "verify.py").read_text(encoding="utf-8"))
    return {
        t.id: ast.literal_eval(n.value)
        for n in tree.body
        if isinstance(n, ast.Assign)
        for t in n.targets
        if isinstance(t, ast.Name) and isinstance(n.value, ast.Constant)
    }


def test_prompt_states_the_exact_edits_the_grader_expects():
    consts = _verify_constants()
    prompt = (TASK / "fixture" / "SPEC.md").read_text("utf-8")
    for needle in (consts["OLD_VERSION"], consts["NEW_VERSION"], consts["ENTRY"], consts["ROW"]):
        assert f"`{needle}`" in prompt, needle
    assert consts["ANCHOR_KEY"] in prompt
    ref = (TASK / "solutions" / "reference" / "solve.py").read_text("utf-8")
    assert consts["ENTRY"].lstrip(" ") in ref and consts["ROW"] in ref


def test_verify_app_default_is_container_path():
    tree = ast.parse((TASK / "tests" / "verify.py").read_text(encoding="utf-8"))
    (assign,) = [
        n
        for n in tree.body
        if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "APP" for t in n.targets)
    ]
    call = assign.value
    assert isinstance(call, ast.Call) and call.args[0].value == "KILMEH_APP"
    assert call.args[1].value == "/app"


def test_verify_never_runs_agent_code_and_never_writes_bytecode():
    source = (TASK / "tests" / "verify.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module)
    assert not imported & {"importlib", "runpy", "imp", "pickle", "marshal"}
    calls = {ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert not calls & {"exec", "eval", "compile", "__import__", "os.system"}
    assert "sys.dont_write_bytecode = True" in source
    assert source.index("sys.dont_write_bytecode") < source.index("def unlocked_path")


def test_main_sweeps_nobody_before_and_after_reading_the_app():
    tree = ast.parse((TASK / "tests" / "verify.py").read_text(encoding="utf-8"))
    (main,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main"]
    body = [ast.unparse(n) for n in main.body]
    sweeps = [i for i, line in enumerate(body) if line == "sweep()"]
    (read,) = [i for i, line in enumerate(body) if "read_app(name)" in line]
    (lock,) = [i for i, line in enumerate(body) if "unlocked_path(HERE)" in line]
    assert len(sweeps) == 2 and lock < sweeps[0] < read < sweeps[1]


def test_test_sh_order_and_hardening():
    lines = (TASK / "tests" / "test.sh").read_text("utf-8").splitlines()
    assert "export PYTHONDONTWRITEBYTECODE=1" in lines
    zero = lines.index("echo 0 > /logs/verifier/reward.txt")
    readable = lines.index("chmod -R a+rX /app")
    lock = lines.index("if ! chown -R 0:0 /tests || ! chmod -R go-rwx /tests; then")
    verify = next(i for i, ln in enumerate(lines) if "/tests/verify.py" in ln)
    assert zero < readable < lock < verify
    assert "python3 -B -I -S /tests/verify.py" in lines[verify]
    assert ">&2" in lines[lock + 1] and lines[lock + 2] == "  exit 1"
    after = lines[verify + 1 :]
    assert "  echo 1 > /logs/verifier/reward.txt" in after
    assert "  echo 0 > /logs/verifier/reward.txt" in after


def test_reference_passes(app):
    apply(TASK / "solutions" / "reference", app)
    rc, result = run_verify(TASK, app)
    assert set(result) == CHECKS
    assert failing(result) == set()
    assert rc == 0


def test_known_bad_fails(app):
    apply(TASK / "solutions" / "known-bad", app)
    rc, result = run_verify(TASK, app)
    assert failing(result) == KNOWN_BAD_FAILS
    assert rc == 1


def test_reference_logs_a_pass_line_per_check(app):
    apply(TASK / "solutions" / "reference", app)
    proc = run_verify_raw(TASK, app)
    assert check_lines(proc.stderr) == [("PASS", k) for k in json.loads(proc.stdout)]


def test_known_bad_logs_a_fail_line_for_a_failed_check(app):
    apply(TASK / "solutions" / "known-bad", app)
    proc = run_verify_raw(TASK, app)
    report = json.loads(proc.stdout)
    lines = check_lines(proc.stderr)
    assert [k for _, k in lines] == list(report)
    assert {k for v, k in lines if v == "FAIL"} == failing(report) != set()


def test_untouched_fixture_fails(app):
    rc, result = run_verify(TASK, app)
    assert failing(result) == UNTOUCHED_FAILS
    assert rc == 1


def test_one_mutation_per_check():
    assert {p.stem for p in MUTATIONS.glob("*.py")} == CHECKS == set(MUTATION_FAILS)


@pytest.mark.parametrize("check", sorted(CHECKS))
def test_each_check_fails_in_isolation(app, check):
    apply(TASK / "solutions" / "reference", app)
    apply(MUTATIONS / f"{check}.py", app)
    rc, result = run_verify(TASK, app)
    assert check in failing(result)
    assert failing(result) == MUTATION_FAILS[check]
    assert rc == 1


def test_two_alternatives_exist():
    assert len(list(ALTERNATIVES.glob("*.py"))) == 2


@pytest.mark.parametrize("alt", sorted(p.stem for p in ALTERNATIVES.glob("*.py")))
def test_alternative_scores_1(app, alt):
    apply(ALTERNATIVES / f"{alt}.py", app)
    rc, result = run_verify(TASK, app)
    assert failing(result) == set()
    assert rc == 0


def test_every_gaming_script_is_listed():
    assert {p.stem for p in GAMING_DIR.glob("*.py")} == set(GAMING)


@pytest.mark.parametrize("game", sorted(GAMING))
def test_gaming_scores_0(app, game):
    needs_reference, expected = GAMING[game]
    if needs_reference:
        apply(TASK / "solutions" / "reference", app)
    apply(GAMING_DIR / f"{game}.py", app)
    rc, result = run_verify(TASK, app)
    assert set(result) == CHECKS
    assert failing(result) == expected
    assert rc == 1


def test_a_missing_file_scores_0(app):
    apply(TASK / "solutions" / "reference", app)
    (app / "README.md").unlink()
    rc, result = run_verify(TASK, app)
    assert failing(result) == CHECKS
    assert rc == 1


def test_a_fifo_at_an_app_path_scores_0_quickly(app):
    """O_NONBLOCK: opening a FIFO must not hang the grader until a timeout."""
    apply(TASK / "solutions" / "reference", app)
    (app / "README.md").unlink()
    os.mkfifo(app / "README.md")
    start = time.monotonic()
    rc, result = run_verify(TASK, app)
    assert time.monotonic() - start < 10
    assert failing(result) == CHECKS
    assert rc == 1


def _pad_readme(app, size: int) -> None:
    readme = app / "README.md"
    data = readme.read_bytes()
    readme.write_bytes(data + b"x" * (size - len(data)))


def test_a_file_over_the_size_cap_scores_0_on_every_check(app):
    """read_app refuses a file over MAX_BYTES, so every check fails, not only readme_unchanged."""
    apply(TASK / "solutions" / "reference", app)
    _pad_readme(app, _verify_constants()["MAX_BYTES"] + 1)
    rc, result = run_verify(TASK, app)
    assert failing(result) == CHECKS
    assert rc == 1


def test_a_file_exactly_at_the_size_cap_is_still_read(app):
    """The cap is inclusive: MAX_BYTES itself is graded, so only the README check fails."""
    apply(TASK / "solutions" / "reference", app)
    _pad_readme(app, _verify_constants()["MAX_BYTES"])
    rc, result = run_verify(TASK, app)
    assert failing(result) == {"readme_unchanged"}
    assert rc == 1


def test_verify_refuses_readable_grader_files(app):
    """Fail closed: a tests/ copy that others can read is refused before the app is read."""
    apply(TASK / "solutions" / "reference", app)
    proc = run_verify_raw(TASK, app, lock=False)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert "refusing to grade" in proc.stderr
    assert run_verify_raw(TASK, app, lock=True).returncode == 0


def test_the_grade_reads_one_snapshot_up_front():
    """read_app runs for all three files before grade() starts: no later write can matter."""
    source = (TASK / "tests" / "verify.py").read_text(encoding="utf-8")
    assert "app = {name: read_app(name) for name in FILES}" in source
    assert source.index("read_app(name) for name") < source.index("report = grade(app, gold)")


# In-image cases: one container, each case on a fresh copy of /app, graded exactly as the
# self-test grades (root, network off). Prints one line per case.
IMAGE_SCRIPT = r"""
cp -a /app /pristine
nobody_alive() { grep -l '^Uid:[[:space:]]*65534' /proc/[0-9]*/status 2>/dev/null | head -1; }
case_run() {
  name=$1; shift
  find /app -mindepth 1 -delete; cp -a /pristine/. /app/
  for step in "$@"; do (cd /app && bash -c "$step") >/dev/null 2>&1; done
  bash /tests/test.sh >/dev/null 2>&1
  sleep 2
  reward=$(cat /logs/verifier/reward.txt 2>/dev/null | tr -d '\n')
  alive=no; [ -n "$(nobody_alive)" ] && alive=yes
  perms=$(stat -c '%u:%a' /logs/verifier /logs/verifier/reward.txt 2>/dev/null | tr '\n' ' ')
  echo "CASE|$name|$reward|$alive|$perms"
}
case_run reference "bash /solutions/reference/solve.sh"
case_run known_bad "bash /solutions/known-bad/solve.sh"
case_run untouched
case_run planted_reward "python3 /extra/plant_reward.py"
case_run open_logs_dir "mkdir -p /logs/verifier && chmod 777 /logs/verifier" \
  "python3 /extra/plant_reward.py"
case_run nobody_daemon "bash /solutions/reference/solve.sh" "python3 /extra/nobody_daemon.py"
"""

PLANT_REWARD = """import os
import pathlib

os.makedirs("/logs/verifier", exist_ok=True)
pathlib.Path("/logs/verifier/reward.txt").write_text("1\\n")
pathlib.Path("/logs/verifier/checks.json").write_text('{"all": true}')
"""

NOBODY_DAEMON = """import os
import time

if os.fork() == 0:
    os.setsid()
    os.setgid(65534)
    os.setuid(65534)
    time.sleep(600)
"""


@pytest.fixture(scope="module")
def image_cases(tmp_path_factory):
    extra = tmp_path_factory.mktemp("extra")
    (extra / "plant_reward.py").write_text(PLANT_REWARD, encoding="utf-8")
    (extra / "nobody_daemon.py").write_text(NOBODY_DAEMON, encoding="utf-8")
    mounts = {TASK / "solutions": "/solutions", extra: "/extra"}
    out = run_in_image(TASK, IMAGE_SCRIPT, mounts)
    cases = {}
    for line in out.splitlines():
        if line.startswith("CASE|"):
            _, name, reward, alive, perms = line.split("|", 4)
            cases[name] = {"reward": reward, "alive": alive, "perms": perms}
    return cases


@pytest.mark.docker
def test_in_image_scores(image_cases):
    assert image_cases["reference"]["reward"] == "1"
    assert image_cases["known_bad"]["reward"] == "0"
    assert image_cases["untouched"]["reward"] == "0"


@pytest.mark.docker
def test_in_image_planted_reward_is_overwritten(image_cases):
    assert image_cases["planted_reward"]["reward"] == "0"


@pytest.mark.docker
def test_in_image_open_logs_dir_is_relocked(image_cases):
    case = image_cases["open_logs_dir"]
    assert case["reward"] == "0"
    assert case["perms"].split() == ["0:755", "0:644"]


@pytest.mark.docker
def test_in_image_uid_65534_daemon_is_swept_and_reference_still_scores_1(image_cases):
    case = image_cases["nobody_daemon"]
    assert case["alive"] == "no", "the daemon outlived the grader"
    assert case["reward"] == "1"


SED_PRINTF_SOLUTION = r"""#!/bin/bash
# QA alternative (b): sed -i for the version and the insert, printf for the CSV row.
set -e
cd /app
sed -i 's/"2\.3\.0"/"2.4.0"/' src/strings.ts
sed -i '/^  checkout_title:/a\  checkout_subtitle: "راجع طلبك قبل الدفع",' src/strings.ts
printf 'checkout_subtitle,راجع طلبك قبل الدفع\r\n' >> locale/ar.csv
"""


@pytest.mark.docker
def test_in_image_sed_and_printf_alternative_scores_1(tmp_path):
    sol = tmp_path / "sed_printf"
    sol.mkdir()
    (sol / "solve.sh").write_text(SED_PRINTF_SOLUTION, encoding="utf-8")
    result = selftest.docker_runner(TASK, sol, 120)
    assert result.reward == 1, result.detail
