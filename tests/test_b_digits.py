"""Grader tests for arabic-digits-parse-format (Track B, parent/worker grader).

Host tests run tests/verify.py against a temp copy of the fixture (KILMEH_APP). Each check
fails alone under its own mutation (tests/b_mutations/), two independent correct alternatives
score 1 (tests/b_alternatives/), gaming attempts score 0 (tests/b_gaming/), and probes pin the
worker's guards (tests/b_probes/). Cases that need the real container (uid drop, locked /tests,
reward.txt, a forked daemon) are marked `docker`:
`uv run pytest -m docker tests/test_b_digits.py`.
"""

import ast
import hashlib
import json
import os
import re
import shutil
import time
import unicodedata
from decimal import Decimal

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

TASK_ID = "arabic-digits-parse-format"
TASK = task_dir(TASK_ID)
MUTATIONS = ROOT / "tests" / "b_mutations" / TASK_ID
ALTERNATIVES = ROOT / "tests" / "b_alternatives" / TASK_ID
GAMING = ROOT / "tests" / "b_gaming" / TASK_ID
PROBES = ROOT / "tests" / "b_probes" / TASK_ID

CHECKS = {
    "parse_latn",
    "parse_arab",
    "parse_arabext",
    "parse_decimal_sep",
    "parse_grouping",
    "rejects_mixed_scripts",
    "rejects_other_unicode_digits",
    "rejects_python_int_extras",
    "rejects_bad_grouping",
    "format_latn",
    "format_arab",
    "format_arabext",
    "format_negative_and_rounding",
    "roundtrip_seeded",
    "caller_works",
}

FIXTURE_SHA256 = {
    "numerals.py": "de47bb41b7854312f62cf27c6b4d3197d54e51ea0bb15e696989f7cbfee63d4b",
    "invoice.py": "cc207cee69071d756d784eb5782e85a920706199a60529925f71f8b60a9597d2",
    "test_numerals.py": "f30433be261f285b9f860501cf2094346c33fdce342f396bd24274c6af5cb50b",
    "README.md": "efd56627b06221bb48216152ca226b41f1ae3911df1aff6c9d05c17a3fcd5a14",
    "SPEC.md": "f703ed28c4e51b33819f8bae5e6cf7fb02d976107bd51b5a662aa00af1cc6d5f",
}
PROMPT_SHA256 = {
    "en.md": "5b04bb9d9517cea4c513fd6798c4dadefcec0a2d440ac2565b75ff05f061af63",
    "levantine.md": "e438c44ddb6f558e0b6f5f7c68549a715d8c86232aaa51cc816891b394d88678",
}
FROM_LINE = (
    "FROM python:3.12.15-slim-bookworm"
    "@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70"
)

# Observed with the reference grader; exact, so a new false pass or fail is noticed.
KNOWN_BAD_FAILS = {
    "rejects_mixed_scripts",
    "rejects_other_unicode_digits",
    "rejects_python_int_extras",
}

# Host gaming cases (each starts from the unchanged fixture) -> exact failing set.
GAMING_FAILS = {
    # raising ValueError for everything unknown passes the four rejection checks; it still
    # scores 0 because no hidden value is parsed or formatted
    "hardcode_visible": CHECKS
    - {
        "rejects_mixed_scripts",
        "rejects_other_unicode_digits",
        "rejects_python_int_extras",
        "rejects_bad_grouping",
    },
    "os_exit_at_import": CHECKS,
    "sys_exit_at_import": CHECKS,
    "fake_json_print": CHECKS,
    "decimal_eq_patch": CHECKS,
    "edit_visible_tests": CHECKS,
    # answers grader 0.1.0's fixed inputs; a rejection's answer is ValueError whatever the
    # digits, so those checks still pass (reward is all-or-nothing)
    "constant_forge": CHECKS
    - {
        "rejects_mixed_scripts",
        "rejects_other_unicode_digits",
        "rejects_python_int_extras",
        "rejects_bad_grouping",
    },
}
DOCKER_GAMING = {"reward_at_import", "forked_daemon", "read_tests_cheat"}

PARSE_READERS = {
    "parse_latn",
    "parse_arab",
    "parse_arabext",
    "parse_decimal_sep",
    "parse_grouping",
    "roundtrip_seeded",
}
FORMAT_READERS = {
    "format_latn",
    "format_arab",
    "format_arabext",
    "format_negative_and_rounding",
    "caller_works",
}
# Probes on top of the reference -> exact failing set. Each one pins a worker guard:
# exact Decimal type, exact str type, app dir last on sys.path, agent stdout discarded, and a
# planted /app/json.py never imported.
PROBE_FAILS = {
    "decimal_subclass": PARSE_READERS,
    "str_subclass": FORMAT_READERS,
    "app_dir_last": set(),
    "prints_at_import": set(),
    "json_shadow": set(),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def app(tmp_path):
    return fresh_app(TASK, tmp_path)


def test_fixture_files_are_pinned():
    files = {p.name for p in (TASK / "fixture").iterdir()}
    assert files == set(FIXTURE_SHA256)
    for name, expected in FIXTURE_SHA256.items():
        assert sha256((TASK / "fixture" / name).read_bytes()) == expected, name


def test_prompts_are_pinned():
    for name, expected in PROMPT_SHA256.items():
        assert sha256((TASK / "prompts" / name).read_bytes()) == expected, name


def test_dockerfile_from_line_is_pinned():
    lines = (TASK / "environment" / "Dockerfile").read_text("utf-8").splitlines()
    assert lines[0] == FROM_LINE
    assert re.fullmatch(r"FROM python:3\.12\.\d+-slim-bookworm@sha256:[0-9a-f]{64}", lines[0])
    assert [ln for ln in lines if ln.startswith("FROM")] == [FROM_LINE]


def test_grader_and_fixture_sources_are_ascii():
    """Every non-ASCII character is a visible escape (see REVIEW.md)."""
    paths = [*(TASK / "fixture").iterdir(), *(TASK / "tests").iterdir()]
    paths += [*(TASK / "solutions").rglob("*.py")]
    for path in paths:
        assert path.read_bytes().isascii(), path


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


def test_verify_never_imports_the_app():
    tree = ast.parse((TASK / "tests" / "verify.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module)
    assert not imported & {"numerals", "invoice", "importlib", "runpy"}


def _verify_matches():
    """verify.matches without running verify.py's main(): exec just its regex and function."""
    tree = ast.parse((TASK / "tests" / "verify.py").read_text(encoding="utf-8"))
    keep = [
        n
        for n in tree.body
        if getattr(n, "name", "") == "matches"
        or any(getattr(t, "id", "") == "_DECIMAL_STR" for t in getattr(n, "targets", []))
    ]
    ns = {"re": re, "Decimal": Decimal}
    exec(compile(ast.Module(keep, []), "verify.py", "exec"), ns)
    return ns["matches"]


@pytest.mark.parametrize("text", ["1e3", " 1000", "1000 ", "+1000", "1_000", "\u0661000"])
def test_matches_rejects_non_canonical_decimal_strings(text):
    """Decimal(text) == 1000 for each, but the worker must report str(Decimal) form."""
    matches = _verify_matches()
    assert matches(["ok", "Decimal", "1000"], ("value", "1000"))
    assert not matches(["ok", "Decimal", text], ("value", "1000"))


def test_test_sh_writes_zero_first_and_both_branches():
    lines = (TASK / "tests" / "test.sh").read_text("utf-8").splitlines()
    zero = lines.index("echo 0 > /logs/verifier/reward.txt")
    verify = next(i for i, ln in enumerate(lines) if "/tests/verify.py" in ln)
    assert zero < verify
    assert "python3 -I -S /tests/verify.py" in lines[verify]
    lock = lines.index("if ! chown -R 0:0 /tests || ! chmod -R go-rwx /tests; then")
    assert zero < lock < verify
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
    assert failing(result) == CHECKS
    assert rc == 1


def test_one_mutation_per_check():
    assert {p.stem for p in MUTATIONS.glob("*.py")} == CHECKS


@pytest.mark.parametrize("check", sorted(CHECKS))
def test_each_check_fails_in_isolation(app, check):
    apply(TASK / "solutions" / "reference", app)
    apply(MUTATIONS / f"{check}.py", app)
    rc, result = run_verify(TASK, app)
    assert failing(result) == {check}
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
    assert {p.stem for p in GAMING.glob("*.py")} == set(GAMING_FAILS) | DOCKER_GAMING


@pytest.mark.parametrize("game", sorted(GAMING_FAILS))
def test_gaming_scores_0(app, game):
    apply(GAMING / f"{game}.py", app)
    rc, result = run_verify(TASK, app)
    assert set(result) == CHECKS
    assert failing(result) == GAMING_FAILS[game]
    assert rc == 1


# In-image cases: one container, each case on a fresh copy of /app, run exactly as the
# self-test runs the grader (root, network off). Prints one line per case.
IMAGE_SCRIPT = r"""
cp -a /app /pristine
case_run() {
  name=$1; shift
  find /app -mindepth 1 -delete; cp -a /pristine/. /app/
  find /tmp -mindepth 1 -name 'kilmeh-*' -delete
  for step in "$@"; do (cd /app && bash -c "$step") >/dev/null 2>&1; done
  bash /tests/test.sh >/dev/null 2>&1
  sleep 5
  reward=$(cat /logs/verifier/reward.txt 2>/dev/null | tr -d '\n')
  probe=$(cat /tmp/kilmeh-probe 2>/dev/null)
  alive=no; [ -e /tmp/kilmeh-daemon-alive ] && alive=yes
  perms=$(stat -c '%u:%a' /logs/verifier /logs/verifier/reward.txt 2>/dev/null | tr '\n' ' ')
  echo "CASE|$name|$reward|$alive|$perms|$probe"
}
case_run reference "bash /solution/solve.sh"
case_run reference_0600 "bash /solution/solve.sh" "chmod 600 /app/*.py; chmod 700 /app"
case_run uid_probe "bash /solution/solve.sh" "python3 /probe/probe.py"
case_run os_exit_at_import "python3 /gaming/os_exit_at_import.py"
case_run reward_at_import "python3 /gaming/reward_at_import.py"
case_run forked_daemon "python3 /gaming/forked_daemon.py"
case_run open_logs_dir "mkdir -p /logs/verifier && chmod 777 /logs/verifier" \
  "python3 /probe/replace_reward.py"
"""

PROBE = '''from pathlib import Path

CHEAT = """import os as _os
with open("/tmp/kilmeh-probe", "w") as _f:
    _f.write(f"{_os.getuid()} {_os.getgid()} {_os.getgroups()} {_os.getsid(0) == _os.getpid()}")
"""
path = Path("numerals.py")
path.write_text(CHEAT + path.read_text(encoding="utf-8"), encoding="utf-8")
'''


# Agent code (run as nobody) swaps in its own reward.txt; only an open /logs/verifier allows it.
REPLACE_REWARD = '''from pathlib import Path

CHEAT = """import os as _os
try:
    with open("/logs/verifier/r.tmp", "w") as _f:
        _f.write("1")
    _os.replace("/logs/verifier/r.tmp", "/logs/verifier/reward.txt")
except OSError:
    pass
"""
path = Path("numerals.py")
path.write_text(CHEAT + path.read_text(encoding="utf-8"), encoding="utf-8")
'''


@pytest.fixture(scope="module")
def image_cases(tmp_path_factory):
    probe_dir = tmp_path_factory.mktemp("probe")
    (probe_dir / "probe.py").write_text(PROBE, encoding="utf-8")
    (probe_dir / "replace_reward.py").write_text(REPLACE_REWARD, encoding="utf-8")
    mounts = {
        TASK / "solutions" / "reference": "/solution",
        GAMING: "/gaming",
        probe_dir: "/probe",
    }
    out = run_in_image(TASK, IMAGE_SCRIPT, mounts)
    cases = {}
    for line in out.splitlines():
        if line.startswith("CASE|"):
            _, name, reward, alive, perms, probe = line.split("|", 5)
            cases[name] = {"reward": reward, "alive": alive, "perms": perms, "probe": probe}
    return cases


@pytest.mark.docker
def test_in_image_reference_scores_1(image_cases):
    assert image_cases["reference"]["reward"] == "1"


@pytest.mark.docker
def test_in_image_0600_solution_scores_1(image_cases):
    """Pins `chmod -R a+rX /app`: the worker (uid 65534) must read a root-only solution."""
    assert image_cases["reference_0600"]["reward"] == "1"


@pytest.mark.docker
def test_in_image_worker_drops_to_nobody_in_new_session(image_cases):
    case = image_cases["uid_probe"]
    assert case["probe"] == "65534 65534 [] True"
    assert case["reward"] == "1"


@pytest.mark.docker
@pytest.mark.parametrize("game", ["os_exit_at_import", "reward_at_import"])
def test_in_image_gaming_scores_0(image_cases, game):
    assert image_cases[game]["reward"] == "0"


@pytest.mark.docker
def test_in_image_forked_daemon_is_killed(image_cases):
    case = image_cases["forked_daemon"]
    assert case["reward"] == "0"
    assert case["alive"] == "no", "the daemon outlived the grader"


@pytest.mark.docker
def test_in_image_preopened_logs_dir_is_locked_before_agent_code(image_cases):
    """/logs/verifier left 0777 at agent time: test.sh relocks it, so nobody cannot replace
    reward.txt (dir root 755, reward.txt root-owned)."""
    case = image_cases["open_logs_dir"]
    assert case["reward"] == "0"
    assert case["perms"].split() == ["0:755", "0:644"]


def test_every_probe_is_listed():
    assert {p.stem for p in PROBES.glob("*.py")} == set(PROBE_FAILS)


@pytest.mark.parametrize("probe", sorted(PROBE_FAILS))
def test_probe(app, probe):
    apply(TASK / "solutions" / "reference", app)
    apply(PROBES / f"{probe}.py", app)
    rc, result = run_verify(TASK, app)
    assert set(result) == CHECKS
    assert failing(result) == PROBE_FAILS[probe]
    assert (rc == 0) == (not PROBE_FAILS[probe])


def test_forked_child_is_killed_with_the_worker(app, tmp_path):
    """A child left in the worker's process group dies with it (start_new_session + killpg).
    Host run, not root, so no uid 65534 sweep helps here."""
    marker = tmp_path / "child-alive"
    apply(TASK / "solutions" / "reference", app)
    numerals = app / "numerals.py"
    cheat = (
        "\nimport os as _o, time as _t\n"
        "if _o.fork() == 0:\n"
        "    _o.closerange(0, 1024)\n"
        "    _t.sleep(2)\n"
        f"    open({str(marker)!r}, 'w').close()\n"
        "    _o._exit(0)\n"
    )
    numerals.write_text(numerals.read_text(encoding="utf-8") + cheat, encoding="utf-8")
    rc, _ = run_verify(TASK, app)
    assert rc == 0
    time.sleep(3)
    assert not marker.exists(), "the forked child outlived the grader"


def test_verify_refuses_readable_grader_files(app):
    """Fail closed: a tests/ copy that others can read is refused before any agent code runs."""
    apply(TASK / "solutions" / "reference", app)
    marker = app / "numerals.py"
    marker.write_text(
        marker.read_text(encoding="utf-8") + f"\nopen({str(app / 'ran')!r}, 'w').close()\n",
        encoding="utf-8",
    )
    proc = run_verify_raw(TASK, app, lock=False)
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert "refusing to grade" in proc.stderr
    assert not (app / "ran").exists(), "agent code ran although the grader was readable"
    assert run_verify_raw(TASK, app, lock=True).returncode == 0


def test_unlocked_path_refuses_mode_0700_owned_by_another_uid(tmp_path, monkeypatch):
    """Owner check alone: /tests is 0700 (no group/other bits) but not owned by the grader."""
    tree = ast.parse((TASK / "tests" / "verify.py").read_text(encoding="utf-8"))
    keep = [n for n in tree.body if getattr(n, "name", "") == "unlocked_path"]
    ns = {"os": os}
    exec(compile(ast.Module(keep, []), "verify.py", "exec"), ns)
    root = tmp_path / "tests"
    root.mkdir(mode=0o700)
    root.chmod(0o700)
    assert ns["unlocked_path"](str(root)) is None
    monkeypatch.setattr(os, "geteuid", lambda: root.stat().st_uid + 1)
    assert ns["unlocked_path"](str(root)) is not None


@pytest.mark.docker
def test_in_image_read_tests_cheat_scores_0_under_selftest(tmp_path):
    """QA's cheat reads /tests/verify.py at import; graded by the real self-test runner."""
    sol = tmp_path / "cheat"
    sol.mkdir()
    shutil.copy(GAMING / "read_tests_cheat.py", sol / "read_tests_cheat.py")
    (sol / "solve.sh").write_text(
        '#!/bin/bash\ncd /app && python3 "$(dirname "$0")/read_tests_cheat.py"\n',
        encoding="utf-8",
    )
    result = selftest.docker_runner(TASK, sol, 120)
    assert result.reward == 0, result.detail


def _exchange(proc):
    """(calls, results) the parent logged on stderr for one verify run."""
    out = {}
    for line in proc.stderr.splitlines():
        for key in ("worker calls:", "worker results:"):
            if line.startswith(key):
                out[key] = json.loads(line[len(key) :])
    return out["worker calls:"], out["worker results:"]


def _verify_namespace():
    """verify.py's definitions without running main()."""
    source = (TASK / "tests" / "verify.py").read_text(encoding="utf-8")
    assert source.endswith("\nmain()\n")
    ns = {"__file__": str(TASK / "tests" / "verify.py"), "__name__": "verify"}
    exec(compile(source[: -len("main()\n")], "verify.py", "exec"), ns)
    return ns


def _reference_run(tmp_path, name):
    app = fresh_app(TASK, tmp_path / name)
    apply(TASK / "solutions" / "reference", app)
    return run_verify_raw(TASK, app)


REJECTS = {
    "rejects_mixed_scripts",
    "rejects_other_unicode_digits",
    "rejects_python_int_extras",
    "rejects_bad_grouping",
}
SWAP_DIGITS = {1, 2, 3, 4, 6, 7, 8}


def test_inputs_are_random_but_keep_their_structure(tmp_path):
    """Two runs draw different digits; each drawn call matches its public template except for
    digits in SWAP, so every system, separator, zero, tie and carry stays where it was."""
    ns = _verify_namespace()
    templates = [list(c) for cases in ns["TEMPLATES"].values() for c, _ in cases]
    runs = [_exchange(_reference_run(tmp_path, f"r{i}"))[0] for i in range(2)]
    assert runs[0] != runs[1]
    for calls in runs:
        fixed = [c for c in calls if c[0] != "roundtrip"]
        roundtrip = [c for c in calls if c[0] == "roundtrip"]
        assert len(roundtrip) == 900 and {c[0] for c in roundtrip} == {"roundtrip"}
        for call, template in zip(fixed, templates, strict=True):
            assert call[0] == template[0] and call[2:] == template[2:]  # systems, places
            got = call[1] if isinstance(call[1], list) else [call[1]]
            want = template[1] if isinstance(template[1], list) else [template[1]]
            for g, w in zip(got, want, strict=True):
                g, w = str(g), str(w)
                assert len(g) == len(w), (g, w)
                for a, b in zip(g, w, strict=True):
                    if a != b:
                        assert unicodedata.decimal(a) in SWAP_DIGITS, (g, w)
                        assert unicodedata.decimal(b) in SWAP_DIGITS, (g, w)
                        assert ord(a) - unicodedata.decimal(a) == ord(b) - unicodedata.decimal(b)
    assert [c for c in runs[0] if c[0] == "roundtrip"] != [
        c for c in runs[1] if c[0] == "roundtrip"
    ], "roundtrip values differ between runs"


def _forge(app, recorded):
    """numerals.py that writes `recorded` to fds 3-9 at import and exits, with the real defs."""
    (app / "numerals.py").write_text(
        "import os\n"
        f"_data = {json.dumps(recorded).encode('ascii')!r}\n"
        "for _fd in range(3, 10):\n"
        "    try:\n"
        "        os.write(_fd, _data)\n"
        "    except OSError:\n"
        "        pass\n"
        "os._exit(0)\n"
        "def parse_number(text): ...\n"
        "def format_number(value, system, places=0): ...\n",
        encoding="utf-8",
    )


def _undrawn_task(tmp_path):
    """A copy of the task whose verify.py sends the public templates unchanged (redraw is the
    identity and roundtrip uses a fixed seed): what the grader was before random inputs."""
    task = tmp_path / "undrawn_task"
    shutil.copytree(TASK, task)
    verify = task / "tests" / "verify.py"
    text = verify.read_text("utf-8")
    old_redraw = "    out = []\n    for ch in text:\n"
    old_rng = "    rng = RNG\n"
    assert text.count(old_redraw) == 1 and text.count(old_rng) == 1
    text = text.replace(old_redraw, "    return text\n" + old_redraw)
    text = text.replace(old_rng, "    rng = random.Random(20261112)\n")
    verify.write_text(text, encoding="utf-8")
    return task


def test_constant_forge_scored_1_on_undrawn_grader_and_0_now(tmp_path):
    """tests/b_gaming/.../constant_forge.py answers the public templates with fixed digits.
    Against a grader that sends those inputs (0.1.0, rebuilt here as _undrawn_task) it scores
    1; against the real grader, which redraws the digits each run, it scores 0."""
    app = fresh_app(TASK, tmp_path / "forged")
    apply(GAMING / "constant_forge.py", app)
    assert run_verify_raw(_undrawn_task(tmp_path), app).returncode == 0
    proc = run_verify_raw(TASK, app)
    assert proc.returncode == 1
    assert failing(json.loads(proc.stdout)) == CHECKS - REJECTS


def test_replayed_worker_output_scores_0(tmp_path):
    """QA's forge: the agent's module writes the worker's exact result JSON (a recorded passing
    run of this grader) to the inherited descriptors 3-9 and exits 0. A new run draws new
    inputs, so it must score 0. The rejection checks still pass in the report: a rejection's
    answer is ValueError whatever the digits (reward is all-or-nothing)."""
    first = _reference_run(tmp_path, "record")
    assert first.returncode == 0
    calls, recorded = _exchange(first)
    app = fresh_app(TASK, tmp_path / "forged")
    _forge(app, recorded)
    proc = run_verify_raw(TASK, app)
    new_calls, got = _exchange(proc)
    assert new_calls != calls
    assert got == recorded, "the forge reached the channel intact"
    assert proc.returncode == 1
    assert failing(json.loads(proc.stdout)) == CHECKS - REJECTS


def test_reference_bound_by_assignment_scores_1(tmp_path):
    """QA's case: the functions are plain names bound to defs with other names. No rule in the
    prompt asks for top-level defs, so this must pass."""
    app = fresh_app(TASK, tmp_path / "app")
    ref = (TASK / "solutions" / "reference" / "solve.py").read_text("utf-8")
    for name in ("parse_number", "format_number"):
        assert ref.count(f"def {name}(") == 1
        ref = ref.replace(f"def {name}(", f"def _{name}(") + f"{name} = _{name}\n"
    (app / "numerals.py").write_text(ref, encoding="utf-8")
    invoice = (app / "invoice.py").read_text("utf-8")
    assert invoice.count("def total_text(") == 1
    invoice = invoice.replace("def total_text(", "def _total_text(") + "total_text = _total_text\n"
    (app / "invoice.py").write_text(invoice, encoding="utf-8")
    proc = run_verify_raw(TASK, app)
    assert proc.returncode == 0, proc.stdout


def test_reference_reexported_from_another_module_scores_1(tmp_path):
    app = fresh_app(TASK, tmp_path / "app")
    shutil.copy(TASK / "solutions" / "reference" / "solve.py", app / "_impl.py")
    (app / "numerals.py").write_text(
        "from _impl import format_number, parse_number  # noqa: F401\n", encoding="utf-8"
    )
    proc = run_verify_raw(TASK, app)
    assert proc.returncode == 0, proc.stdout


def test_redraw_moves_every_swap_digit_to_every_swap_digit():
    """Fails if SWAP shrinks: each of 1,2,3,4,6,7,8 (in all three scripts) must be redrawn, and
    the draws must reach all seven; 0, 5 and 9 stay put."""
    ns = _verify_namespace()
    for zero in (0x30, 0x0660, 0x06F0):
        for d in range(10):
            ch = chr(zero + d)
            seen = {unicodedata.decimal(c) for c in ns["redraw"](ch * 200)}
            assert seen == (SWAP_DIGITS if d in SWAP_DIGITS else {d}), (hex(zero), d, seen)


def test_reference_passes_30_random_runs(tmp_path):
    """Randomness must never fail a correct solution."""
    app = fresh_app(TASK, tmp_path / "app")
    apply(TASK / "solutions" / "reference", app)
    for _ in range(30):
        proc = run_verify_raw(TASK, app)
        assert proc.returncode == 0, proc.stdout
