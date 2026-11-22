"""Grader tests for task 001 (arabic-in-code-farewell).

verify.py prints a JSON object with one boolean per check and exits 0 only if all are True.
Each test starts from the fixture or from the reference-solved state, applies one change, and
pins exactly which checks go red.
"""

import ast
import hashlib
import shutil
import subprocess
import sys
import time
import unicodedata
from collections.abc import Callable
from pathlib import Path

import pytest

import b_helpers

TASK = Path(__file__).parent.parent / "tasks" / "b-arabic-in-code" / "arabic-in-code-farewell"
MAIN = "تحية.py"
README = "README.md"
LRI = "⁦"
LAFZ = "ﷲ"

FIXTURE_SHA256 = {
    MAIN: "28fdf6eb169c03745d8da705296de929011ee229a23d83daa2502d333446bf14",
    README: "03259467055b85194fc6639c2b2d574c670794e0b7abca8591417d88b2355381",
}

ALL_KEYS = {
    "no_bom",
    "valid_utf8",
    "orig_lines_byte_identical",
    "bidi_controls_preserved",
    "nfkc_sensitive_char_kept",
    "readme_unchanged",
    "filename_present_exact",
    "farewell_works",
}


def run_verify(app: Path) -> tuple[int, dict[str, bool]]:
    """verify.py run as test.sh runs it, from a locked copy of tests/ (it refuses otherwise)."""
    return b_helpers.run_verify(TASK, app)


def failing(result: dict[str, bool]) -> set[str]:
    return {k for k, v in result.items() if not v}


def solve(app: Path, which: str) -> None:
    script = TASK / "solutions" / which / "solve.py"
    subprocess.run([sys.executable, "-I", str(script), str(app / MAIN)], check=True)


@pytest.fixture
def app(tmp_path: Path) -> Path:
    dest = tmp_path / "app"
    shutil.copytree(TASK / "fixture", dest)
    return dest


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


def test_fixture_files_are_pinned():
    for name, expected in FIXTURE_SHA256.items():
        data = (TASK / "fixture" / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected, name


def test_golden_matches_fixture():
    golden, fixture = TASK / "tests" / "golden", TASK / "fixture"
    assert (golden / "orig.py").read_bytes() == (fixture / MAIN).read_bytes()
    assert (golden / README).read_bytes() == (fixture / README).read_bytes()


def test_reference_passes(app):
    solve(app, "reference")
    rc, result = run_verify(app)
    assert rc == 0
    assert set(result) == ALL_KEYS and all(result.values())


def test_known_bad_fails(app):
    solve(app, "known-bad")
    rc, result = run_verify(app)
    assert rc == 1
    assert failing(result) == {
        "orig_lines_byte_identical",
        "bidi_controls_preserved",
        "nfkc_sensitive_char_kept",
    }


def test_untouched_fixture_fails(app):
    rc, result = run_verify(app)
    assert rc == 1
    assert failing(result) == {"farewell_works"}


FAREWELL_DEF = '\n\ndef farewell(name):\n    return f"وداعاً يا {name}!"\n'


def test_reference_bound_by_assignment_scores_1(app):
    """farewell is a plain name bound to a def with another name. No rule in the prompt asks for
    a top-level def, so this must pass (0.1.1 scored it 0)."""
    add = FAREWELL_DEF.replace("def farewell(", "def _farewell(") + "\nfarewell = _farewell\n"
    edit_main(app, lambda b: b + add.encode())
    rc, result = run_verify(app)
    assert failing(result) == set()
    assert rc == 0


def test_reference_reexported_from_another_module_scores_1(app):
    """Needs the worker's sys.path.append(app) too: 0.1.1 scored it 0 twice over."""
    (app / "_farewell.py").write_text(FAREWELL_DEF, encoding="utf-8")
    edit_main(app, lambda b: b + b"\nfrom _farewell import farewell  # noqa: F401\n")
    rc, result = run_verify(app)
    assert failing(result) == set()
    assert rc == 0


# As tests/b_probes/arabic-digits-parse-format/app_dir_last.py: raises at import unless the
# app directory is on sys.path exactly once, last (after the stdlib).
APP_DIR_LAST = """
import os as _os, sys as _sys
_app = _os.path.dirname(_os.path.abspath(__file__))
_found = [p for p in _sys.path if _os.path.abspath(p) == _app]
if len(_found) != 1 or _os.path.abspath(_sys.path[-1]) != _app:
    raise ImportError("app directory is not last on sys.path")
"""


def test_worker_appends_app_dir_after_the_stdlib(app):
    """Pins sys.path.append(app): insert(0, app) would let an app module shadow the stdlib."""
    solve(app, "reference")
    edit_main(app, lambda b: b + APP_DIR_LAST.encode())
    rc, result = run_verify(app)
    assert failing(result) == set()
    assert rc == 0


def edit_main(app: Path, fn: Callable[[bytes], bytes]) -> None:
    path = app / MAIN
    path.write_bytes(fn(path.read_bytes()))


# Code appended to a correct solution that tries to end or fool the grader at import time.
# The worker imports the app in its own process, so each one only turns farewell_works red.
GAMING = {
    "os_exit_at_import": "import os\nos._exit(0)\n",
    "sys_exit_at_import": "import sys\nsys.exit(0)\n",
    "raise_systemexit_at_import": "raise SystemExit(0)\n",
    "eq_always_true": "farewell = lambda n: type('S', (), {'__eq__': lambda s, o: True})()\n",
}

# QA's attack: write a constant "all correct" answer to every fd the worker may own, then exit.
# Blocked by the per-run random names.
FD_FORGE_CONSTANT = """
import json as _j, os as _o
_E = [[["ok", "وداعاً يا سارة!"], ["ok", "مرحباً بك يا سارة!"]]]
for _fd in range(3, 10):
    try:
        _o.write(_fd, _j.dumps(_E).encode())
    except OSError:
        pass
_o._exit(0)
"""


@pytest.mark.parametrize("game", sorted(GAMING))
def test_gaming_scores_0(app, game):
    solve(app, "reference")
    edit_main(app, lambda b: b + b"\n" + GAMING[game].encode())
    rc, result = run_verify(app)
    assert rc == 1
    assert failing(result) == {"farewell_works"}


def test_forged_worker_output_scores_0(app):
    edit_main(app, lambda b: b + FD_FORGE_CONSTANT.encode())
    rc, result = run_verify(app)
    assert rc == 1
    assert failing(result) == {"farewell_works"}


def test_names_are_random_per_run(app):
    """A forged answer cannot be replayed: two runs try different names."""
    solve(app, "reference")
    logs = [b_helpers.run_verify_raw(TASK, app).stderr for _ in range(2)]
    assert "worker results" in logs[0] and logs[0] != logs[1]


def test_kill_parent_at_import_scores_0(app):
    # off-container the worker shares our uid and can kill verify; test.sh then keeps its 0.
    # In the container it runs as uid 65534 and cannot signal the root grader.
    solve(app, "reference")
    edit_main(app, lambda b: b + b"\nimport os, signal\nos.kill(os.getppid(), signal.SIGKILL)\n")
    proc = b_helpers.run_verify_raw(TASK, app)
    assert proc.returncode != 0


def test_app_json_module_does_not_shadow_the_worker(app):
    """A correct solution with an unrelated /app/json.py still scores 1 (worker runs `-I`, so
    its cwd is not on sys.path)."""
    solve(app, "reference")
    (app / "json.py").write_text("raise ImportError('app json')\n", encoding="utf-8")
    rc, result = run_verify(app)
    assert failing(result) == set()
    assert rc == 0


def test_printing_solution_still_scores_1(app):
    """Pins the worker's dup2(2, 1): the agent's prints go to stderr, not the result channel."""
    solve(app, "reference")
    edit_main(app, lambda b: b + b"\nprint('hello from the app')\n")
    rc, result = run_verify(app)
    assert failing(result) == set()
    assert rc == 0


def test_forked_child_is_killed_with_the_worker(app, tmp_path):
    """A child left in the worker's process group dies with it (start_new_session + killpg).
    Host run, not root, so no uid 65534 sweep helps here."""
    marker = tmp_path / "child-alive"
    solve(app, "reference")
    cheat = (
        "\nimport os as _o, time as _t\n"
        "if _o.fork() == 0:\n"
        "    _o.closerange(0, 1024)\n"
        "    _t.sleep(2)\n"
        f"    open({str(marker)!r}, 'w').close()\n"
        "    _o._exit(0)\n"
    )
    edit_main(app, lambda b: b + cheat.encode())
    rc, _ = run_verify(app)
    assert rc == 0
    time.sleep(3)
    assert not marker.exists(), "the forked child outlived the grader"


def test_verify_refuses_unlocked_tests_dir(app):
    solve(app, "reference")
    proc = b_helpers.run_verify_raw(TASK, app, lock=False)
    assert proc.returncode == 2
    assert "refusing to grade" in proc.stderr


def test_verify_never_imports_the_app():
    src = (TASK / "tests" / "verify.py").read_text(encoding="utf-8")
    assert "importlib" not in src and "exec_module" not in src


def test_test_sh_writes_zero_first_and_both_branches():
    lines = (TASK / "tests" / "test.sh").read_text(encoding="utf-8").splitlines()
    zero = lines.index("echo 0 > /logs/verifier/reward.txt")
    lock = lines.index("if ! chown -R 0:0 /tests || ! chmod -R go-rwx /tests; then")
    verify = next(i for i, line in enumerate(lines) if "/tests/verify.py" in line)
    assert zero < lock < verify
    assert "else echo 0 > /logs/verifier/reward.txt" in lines[verify]


# In-image cases: one container, each case on a fresh /app, graded exactly as the self-test
# grades (root, network off). Each case pins one hardening line; the comment says which.
IMAGE_SCRIPT = r"""
cp -a /app /pristine
SITE=$(python3 -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
case_run() {
  name=$1; shift
  find /app -mindepth 1 -delete; cp -a /pristine/. /app/
  rm -rf /logs /tmp/kilmeh-* "$SITE/sitecustomize.py"
  for step in "$@"; do (cd /app && bash -c "$step") >/dev/null 2>&1; done
  bash /tests/test.sh >/dev/null 2>&1
  sleep 5
  reward=$(cat /logs/verifier/reward.txt 2>/dev/null | tr -d '\n')
  probe=$(cat /tmp/kilmeh-probe 2>/dev/null)
  alive=no; [ -e /tmp/kilmeh-daemon-alive ] && alive=yes
  perms=$(stat -c '%u:%a' /logs/verifier /logs/verifier/reward.txt 2>/dev/null | tr '\n' ' ')
  echo "CASE|$name|$reward|$alive|$perms|$probe"
  rm -rf /tests; cp -a /tests-src /tests
}
cp -a /tests /tests-src
case_run reference "python3 /solution/solve.py"
case_run reference_0600 "python3 /solution/solve.py" "chmod 600 /app/*.py; chmod 700 /app"
case_run fd_forge "python3 /probe/append.py /probe/fd_forge.txt"
case_run uid_probe "python3 /solution/solve.py" "python3 /probe/append.py /probe/uid.txt"
case_run daemon "python3 /probe/append.py /probe/daemon.txt"
case_run sitecustomize "python3 /solution/solve.py" "python3 /probe/append.py /probe/stub.txt" \
  "echo 'import os; os._exit(0)' > $SITE/sitecustomize.py"
case_run nobody_logs_dir "python3 /solution/solve.py" \
  "mkdir -p /logs/verifier && chown 65534:65534 /logs/verifier && chmod 777 /logs/verifier"
"""

APPEND = """import sys
from pathlib import Path

path = Path("تحية.py")
with path.open("a", encoding="utf-8") as f:
    f.write(Path(sys.argv[1]).read_text(encoding="utf-8"))
"""

# Records the worker's uid, gid, groups and whether it leads its own session.
UID_PROBE = """
import os as _o
with open("/tmp/kilmeh-probe", "w") as _f:
    _f.write(f"{_o.getuid()} {_o.getgid()} {_o.getgroups()} {_o.getsid(0) == _o.getpid()}")
"""

# A daemon in a new session that outlives the worker and then writes 1 to reward.txt.
DAEMON = """
import os as _o, time as _t
if _o.fork() == 0:
    _o.setsid()
    if _o.fork() == 0:
        _o.closerange(0, 1024)
        _t.sleep(3)
        for _p in ("/logs/verifier/reward.txt", "/tmp/kilmeh-daemon-alive"):
            try:
                with open(_p, "w") as _f:
                    _f.write("1")
            except OSError:
                pass
    _o._exit(0)
"""

# The stub replaces the reference farewell (the later def wins), so only a hijacked exit code
# could score 1.
STUB = "\ndef farewell(name):\n    return None\n"


@pytest.fixture(scope="module")
def image_cases(tmp_path_factory):
    probe = tmp_path_factory.mktemp("probe")
    for name, text in {
        "append.py": APPEND,
        "fd_forge.txt": FD_FORGE_CONSTANT,
        "uid.txt": UID_PROBE,
        "daemon.txt": DAEMON,
        "stub.txt": STUB,
    }.items():
        (probe / name).write_text(text, encoding="utf-8")
    mounts = {TASK / "solutions" / "reference": "/solution", probe: "/probe"}
    out = b_helpers.run_in_image(TASK, IMAGE_SCRIPT, mounts, timeout=600)
    cases = {}
    for line in out.splitlines():
        if line.startswith("CASE|"):
            _, name, reward, alive, perms, probe_out = line.split("|", 5)
            cases[name] = {"reward": reward, "alive": alive, "perms": perms, "probe": probe_out}
    return cases


@pytest.mark.docker
def test_in_image_reference_scores_1(image_cases):
    assert image_cases["reference"]["reward"] == "1"


@pytest.mark.docker
def test_in_image_0600_solution_scores_1(image_cases):
    """Pins `chmod -R a+rX /app`: the worker (uid 65534) must read a root-only file."""
    assert image_cases["reference_0600"]["reward"] == "1"


@pytest.mark.docker
def test_in_image_fd_forge_scores_0(image_cases):
    assert image_cases["fd_forge"]["reward"] == "0"


@pytest.mark.docker
def test_in_image_worker_drops_to_nobody_in_new_session(image_cases):
    """Pins the uid drop and start_new_session in the container."""
    case = image_cases["uid_probe"]
    assert case["probe"] == "65534 65534 [] True"
    assert case["reward"] == "1"


@pytest.mark.docker
def test_in_image_daemon_is_killed_and_cannot_write_reward(image_cases):
    """Pins the uid drop (a root daemon would write reward.txt) and the uid 65534 sweep (a
    nobody daemon would survive and leave its marker)."""
    case = image_cases["daemon"]
    assert case["reward"] == "0"
    assert case["alive"] == "no", "the daemon outlived the grader"


@pytest.mark.docker
def test_in_image_sitecustomize_cannot_hijack_the_grader(image_cases):
    """Pins `python3 -S` in test.sh: a sitecustomize planted at agent time would otherwise
    run as root inside verify.py and exit 0."""
    assert image_cases["sitecustomize"]["reward"] == "0"


@pytest.mark.docker
def test_in_image_preplanted_logs_dir_is_taken_back(image_cases):
    """Pins `chown 0:0 /logs/verifier`: a dir left owned by 65534 would let the worker swap
    reward.txt."""
    case = image_cases["nobody_logs_dir"]
    assert case["reward"] == "1"
    assert case["perms"].split() == ["0:755", "0:644"]


def mutate_no_bom(app: Path) -> None:
    edit_main(app, lambda b: b"\xef\xbb\xbf" + b)


def mutate_valid_utf8(app: Path) -> None:
    edit_main(app, lambda b: b + b"\xff")


def mutate_orig_line(app: Path) -> None:
    # line 4 is plain code with no bidi control and no U+FDF2
    old = b"def greet(name):"
    edit_main(app, lambda b: b.replace(old, b"def greet(name) :", 1))


def mutate_bidi(app: Path) -> None:
    edit_main(app, lambda b: b.replace(LRI.encode(), b"", 1))


def mutate_nfkc(app: Path) -> None:
    nfkc = unicodedata.normalize("NFKC", LAFZ).encode()
    edit_main(app, lambda b: b.replace(LAFZ.encode(), nfkc, 1))


def mutate_readme(app: Path) -> None:
    with (app / README).open("ab") as f:
        f.write(b" ")


def mutate_filename(app: Path) -> None:
    (app / MAIN).rename(app / "tahiyya.py")


def mutate_farewell(app: Path) -> None:
    # only the appended function changes; every original line stays intact
    edit_main(app, lambda b: b.replace("وداعاً يا".encode(), "مع السلامة يا".encode(), 1))


# name -> (mutation applied to the reference-solved workspace, exact set of red checks).
# Some checks cannot be reached alone; the comments say why.
ISOLATED: dict[str, tuple[Callable[[Path], None], set[str]]] = {
    # a BOM also glues itself to original line 0
    "no_bom": (mutate_no_bom, {"no_bom", "orig_lines_byte_identical"}),
    # an undecodable file cannot be compared line by line, nor counted for bidi controls,
    # and it cannot be imported
    "valid_utf8": (
        mutate_valid_utf8,
        {"valid_utf8", "orig_lines_byte_identical", "bidi_controls_preserved", "farewell_works"},
    ),
    "orig_lines_byte_identical": (mutate_orig_line, {"orig_lines_byte_identical"}),
    # the bidi control sits inside an original line, so that line changes too
    "bidi_controls_preserved": (
        mutate_bidi,
        {"orig_lines_byte_identical", "bidi_controls_preserved"},
    ),
    # the compatibility character sits inside an original line, so that line changes too
    "nfkc_sensitive_char_kept": (
        mutate_nfkc,
        {"orig_lines_byte_identical", "nfkc_sensitive_char_kept"},
    ),
    "readme_unchanged": (mutate_readme, {"readme_unchanged"}),
    # a renamed file reads as empty, so every file-content check fails with it
    "filename_present_exact": (
        mutate_filename,
        {
            "orig_lines_byte_identical",
            "bidi_controls_preserved",
            "nfkc_sensitive_char_kept",
            "filename_present_exact",
            "farewell_works",
        },
    ),
    "farewell_works": (mutate_farewell, {"farewell_works"}),
}


@pytest.mark.parametrize("name", sorted(ISOLATED))
def test_each_check_fails_in_isolation(app, name):
    mutate, expected = ISOLATED[name]
    solve(app, "reference")
    mutate(app)
    rc, result = run_verify(app)
    assert rc == 1
    assert failing(result) == expected
    assert name in expected


def test_isolated_covers_every_check():
    assert set(ISOLATED) == ALL_KEYS


def test_reordered_original_lines_fail(app):
    solve(app, "reference")

    def swap_first_two_lines(data: bytes) -> bytes:
        lines = data.split(b"\n")
        lines[0], lines[1] = lines[1], lines[0]
        return b"\n".join(lines)

    edit_main(app, swap_first_two_lines)
    rc, result = run_verify(app)
    assert rc == 1
    assert failing(result) == {"orig_lines_byte_identical"}


def test_broken_greet_fails(app):
    solve(app, "reference")
    # original lines stay intact; the later definition wins
    edit_main(app, lambda b: b + b"\n\ndef greet(name):\n    return 'x'\n")
    rc, result = run_verify(app)
    assert rc == 1
    assert failing(result) == {"farewell_works"}
