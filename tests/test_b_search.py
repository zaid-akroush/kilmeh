"""Grader tests for arabic-search-normalize (Track B, parent/worker grader).

Host tests run tests/verify.py against a temp copy of the fixture (KILMEH_APP). Each check
fails alone under its own mutation (tests/b_mutations/), two independent correct alternatives
score 1 (tests/b_alternatives/), and gaming attempts score 0 (tests/b_gaming/). The container
cases (uid drop, locked /tests, reward.txt, daemons) are the same parent/worker code as
arabic-digits-parse-format, covered by `uv run pytest -m docker tests/test_b_digits.py` and by
`kilmeh selftest` for this task. This task's own test.sh `chmod -R a+rX /app` is pinned here by
`uv run pytest -m docker tests/test_b_search.py`.
"""

import ast
import hashlib
import json
import re
import shutil
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

TASK_ID = "arabic-search-normalize"
TASK = task_dir(TASK_ID)
MUTATIONS = ROOT / "tests" / "b_mutations" / TASK_ID
ALTERNATIVES = ROOT / "tests" / "b_alternatives" / TASK_ID
GAMING_DIR = ROOT / "tests" / "b_gaming" / TASK_ID

CHECKS = {
    "strips_tashkeel",
    "strips_tatweel",
    "alef_variants",
    "taa_marbuta",
    "alef_maqsura",
    "nfd_input",
    "no_over_normalization",
    "latin_casefold",
    "search_recall_hidden",
    "search_precision_hidden",
    "search_returns_originals",
    "records_not_mutated",
    "sort_order_hidden",
    "sort_returns_originals",
}

FIXTURE_SHA256 = {
    "contacts.py": "d7793ab2cc7eaef36668a034fb2071de6780c82d27693f8229960d2a4830a527",
    "search.py": "0853e22c5efdb814471651e6d3afc9f4db85309e297402f66228b4c3f82014f0",
    "README.md": "8a1aeaa496d31a195a4c1d98ad6778b52862274c1e9bdeb6799da117c42cd8fc",
    "SPEC.md": "30f8e5414008b61840fef770671fe7c66d08b557491bc6e53b20d24a34ed6906",
}
PROMPT_SHA256 = {
    "en.md": "41fe354ffbafb723509ae8475d3275e2404a1d0ab5a4e579a747739da76e726a",
    "levantine.md": "a55b59ce4f35f870849c51488bdaedb6bf40c568cbc63054f3bd13baad5ba982",
}
FROM_LINE = (
    "FROM python:3.12.15-slim-bookworm"
    "@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70"
)

# Observed with the reference grader; exact, so a new false pass or fail is noticed.
KNOWN_BAD_FAILS = {"search_returns_originals", "records_not_mutated", "sort_returns_originals"}

# Gaming cases -> (needs the reference underneath, exact failing set).
ALL = CHECKS
# Gaming cases whose failing set is only a lower bound: the answer is right by chance for some
# random draws (the hard-coded ids can coincide with the random records).
LOWER_BOUND = {"hardcode_visible"}
GAMING = {
    "hardcode_visible": (
        False,
        {
            "strips_tashkeel",
            "strips_tatweel",
            "alef_variants",
            "taa_marbuta",
            "alef_maqsura",
            "nfd_input",
            "latin_casefold",
            "search_recall_hidden",
            "sort_order_hidden",
        },
    ),
    "os_exit_at_import": (False, ALL),
    "fake_json_print": (False, ALL),
    "return_all": (True, {"search_precision_hidden"}),
    "return_empty": (True, {"search_recall_hidden"}),
    "raw_sorted": (True, {"sort_order_hidden"}),
    # same objects, changed content: needs the worker's `r != pristine[idx]` guard for the first
    "mutates_returned": (True, {"search_returns_originals", "records_not_mutated"}),
    # NFKC breaks U+FDF2 (and the decomposed marks, which NFKC composes before they are stripped)
    "nfkc_inputs": (
        True,
        {
            "latin_casefold",
            "nfd_input",
            "no_over_normalization",
            "search_precision_hidden",
        },
    ),
    # NFD then dropping every Mn: U+0624 and U+0626 lose their hamza, and the Latin e + U+0301
    # in latin_casefold loses its accent
    "nfd_strip_all": (
        True,
        {
            "latin_casefold",
            "no_over_normalization",
            "search_precision_hidden",
            "sort_order_hidden",
        },
    ),
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


def test_text_files_are_utf8_without_bom_or_crlf():
    for path in TASK.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            data = path.read_bytes()
            assert not data.startswith(b"\xef\xbb\xbf"), path
            assert b"\r" not in data, path
            data.decode("utf-8")


def test_solutions_and_worker_are_ascii():
    """Every non-ASCII character in code the agent never sees is a visible escape."""
    paths = [*(TASK / "solutions").rglob("*.py"), TASK / "tests" / "worker.py"]
    for path in paths:
        assert path.read_bytes().isascii(), path


def test_invisible_characters_are_escapes_in_sources():
    """Marks (Mn), format characters and tatweel never appear literally in fixture or grader."""
    for path in [TASK / "fixture" / "contacts.py", TASK / "tests" / "verify.py"]:
        for ch in path.read_text("utf-8"):
            bad = unicodedata.category(ch) in ("Mn", "Cf", "Lm") or ch in "ـﷲ"
            assert not bad, f"{path.name}: literal U+{ord(ch):04X}"


def test_mn_ranges_match_python_unicodedata():
    """The Mn list in the prompt and in the reference is what this Python reports."""
    mn = [c for c in range(0x0600, 0x0700) if unicodedata.category(chr(c)) == "Mn"]
    ranges = []
    for c in mn:
        if ranges and ranges[-1][1] == c - 1:
            ranges[-1][1] = c
        else:
            ranges.append([c, c])
    prompt = (TASK / "fixture" / "SPEC.md").read_text("utf-8")
    ref = (TASK / "solutions" / "reference" / "solve.py").read_text("utf-8")
    for lo, hi in ranges:
        assert f"(0x{lo:04X}, 0x{hi:04X})" in ref, (lo, hi)
    for lo, hi in ranges:
        text = f"U+{lo:04X}" if lo == hi else f"U+{lo:04X} to U+{hi:04X}"
        assert text in prompt, text


def test_grader_normalizer_uses_exactly_the_python_mn_set():
    """verify.py's own `norm` (used for search and sort expectations) deletes exactly the Mn
    code points of U+0600-U+06FF plus tatweel, so no range endpoint can drift."""
    tree = ast.parse((TASK / "tests" / "verify.py").read_text(encoding="utf-8"))
    keep = [
        n
        for n in tree.body
        if getattr(n, "name", "") == "norm"
        or (
            not isinstance(n, ast.Import)
            and ast.unparse(n).startswith(("_MN", "_TABLE", "MN_ENDPOINTS"))
        )
    ]
    ns = {}
    exec(compile(ast.Module(keep, []), "verify.py", "exec"), ns)
    mn = {c for c in range(0x0600, 0x0700) if unicodedata.category(chr(c)) == "Mn"}
    assert set(ns["_MN"]) == mn
    assert {c for c, v in ns["_TABLE"].items() if v is None} == mn | {0x0640}
    ends = {c for c in mn if c - 1 not in mn or c + 1 not in mn}
    assert set(ns["MN_ENDPOINTS"]) == ends, "every Mn range endpoint is used in the inputs"


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
    assert not imported & {"search", "contacts", "importlib", "runpy"}


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


@pytest.mark.docker
def test_in_image_0600_solution_scores_1():
    """Pins `chmod -R a+rX /app`: the worker (uid 65534) must read a root-only solution."""
    script = (
        "bash /solution/solve.sh && chmod 600 /app/*.py && chmod 700 /app"
        ' && bash /tests/test.sh >/dev/null 2>&1; echo "REWARD|$(cat /logs/verifier/reward.txt)"'
    )
    out = run_in_image(TASK, script, {TASK / "solutions" / "reference": "/solution"})
    assert "REWARD|1" in out.splitlines(), out


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


def test_reference_bound_by_assignment_scores_1(app):
    """The functions are plain names bound to defs with other names. No rule in the prompt asks
    for top-level defs, so this must pass (0.1.0 scored it 0)."""
    ref = (TASK / "solutions" / "reference" / "solve.py").read_text("utf-8")
    for name in ("normalize_for_search", "search", "sort_names"):
        assert ref.count(f"def {name}(") == 1
        ref = ref.replace(f"def {name}(", f"def _{name}(") + f"{name} = _{name}\n"
    (app / "search.py").write_text(ref, encoding="utf-8")
    rc, result = run_verify(TASK, app)
    assert failing(result) == set()
    assert rc == 0


def test_reference_reexported_from_another_module_scores_1(app):
    shutil.copy(TASK / "solutions" / "reference" / "solve.py", app / "_impl.py")
    (app / "search.py").write_text(
        "from _impl import normalize_for_search, search, sort_names  # noqa: F401\n",
        encoding="utf-8",
    )
    rc, result = run_verify(TASK, app)
    assert failing(result) == set()
    assert rc == 0


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
    assert {p.stem for p in GAMING_DIR.glob("*.py")} == set(GAMING)


@pytest.mark.parametrize("game", sorted(GAMING))
def test_gaming_scores_0(app, game):
    needs_reference, expected = GAMING[game]
    if needs_reference:
        apply(TASK / "solutions" / "reference", app)
    apply(GAMING_DIR / f"{game}.py", app)
    rc, result = run_verify(TASK, app)
    assert set(result) == CHECKS
    if game in LOWER_BOUND:
        assert failing(result) >= expected
    else:
        assert failing(result) == expected
    assert rc == 1


def test_verify_refuses_readable_grader_files(app):
    """Fail closed: a tests/ copy that others can read is refused before any agent code runs."""
    apply(TASK / "solutions" / "reference", app)
    marker = app / "search.py"
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


def _exchange(proc):
    """(calls, results) the parent logged on stderr for one verify run."""
    out = {}
    for line in proc.stderr.splitlines():
        for key in ("worker calls:", "worker results:"):
            if line.startswith(key):
                out[key] = json.loads(line[len(key) :])
    return out["worker calls:"], out["worker results:"]


def _graded_run(tmp_path, name, *scripts):
    app = fresh_app(TASK, tmp_path / name)
    for script in scripts:
        apply(script, app)
    return run_verify_raw(TASK, app)


ENDPOINT_AND_MARK_CODE_POINTS = (
    [0x610, 0x61A, 0x64B, 0x65F, 0x670, 0x6D6, 0x6DC, 0x6DF, 0x6E4, 0x6E7, 0x6E8, 0x6EA, 0x6ED]
    + [0x640, 0x653, 0x654, 0x655, 0x624, 0x626, 0x621, 0xFDF2, 0x623, 0x625, 0x622, 0x671]
    + [0x629, 0x649]
)


def test_inputs_are_random_but_keep_their_structure(tmp_path):
    runs = [
        _exchange(_graded_run(tmp_path, f"r{i}", TASK / "solutions" / "reference"))
        for i in range(2)
    ]
    (calls_a, _), (calls_b, _) = runs
    assert calls_a != calls_b
    for calls in (calls_a, calls_b):
        norms = [c[1] for c in calls if c[0] == "norm"]
        searches = [c for c in calls if c[0] == "search"]
        sorts = [c[1] for c in calls if c[0] == "sort"]
        joined = "".join(norms)
        for cp in ENDPOINT_AND_MARK_CODE_POINTS:
            assert chr(cp) in joined, hex(cp)
        queries = [c[2] for c in searches]
        assert "" in queries and chr(0xFDF2) in queries and "الله" in queries
        assert len(searches[0][1]) >= 30 and len(queries) >= 40
        assert [] in sorts and any(len(x) > 10 for x in sorts)
    searches_a = [c for c in calls_a if c[0] == "search"]
    searches_b = [c for c in calls_b if c[0] == "search"]
    assert searches_a[0][1] != searches_b[0][1], "records differ between runs"
    assert {c[2] for c in searches_a} != {c[2] for c in searches_b}, "queries differ"
    assert [c for c in calls_a if c[0] == "sort"] != [c for c in calls_b if c[0] == "sort"]


def test_constant_forge_replaying_a_previous_run_scores_0(tmp_path):
    """QA's forge: the agent's module writes the worker's exact result JSON to the inherited
    descriptors 3-9 and exits 0. Here the JSON is a recorded passing run, in the right shape
    and length; a new run draws new inputs, so it must score 0."""
    first = _graded_run(tmp_path, "record", TASK / "solutions" / "reference")
    assert first.returncode == 0
    calls, recorded = _exchange(first)
    app = fresh_app(TASK, tmp_path / "forged")
    (app / "search.py").write_text(
        "import os\n"
        f"_data = {json.dumps(recorded).encode('ascii')!r}\n"
        "for _fd in range(3, 10):\n"
        "    try:\n"
        "        os.write(_fd, _data)\n"
        "    except OSError:\n"
        "        pass\n"
        "os._exit(0)\n"
        "def normalize_for_search(s): ...\n"
        "def search(records, query): ...\n"
        "def sort_names(names): ...\n",
        encoding="utf-8",
    )
    proc = run_verify_raw(TASK, app)
    new_calls, got = _exchange(proc)
    assert new_calls != calls
    assert len(got) == len(recorded) == len(new_calls), "the forge reached the channel intact"
    assert got == recorded
    result = json.loads(proc.stdout)
    assert proc.returncode == 1
    assert failing(result) == CHECKS, result


def test_worker_redirects_stdout_to_stderr_before_importing_the_agent(tmp_path):
    """The agent's prints at import must not reach the result channel (os.dup2(2, 1))."""
    printer = tmp_path / "print_at_import.py"
    printer.write_text(
        "from pathlib import Path\n"
        "p = Path('search.py')\n"
        "p.write_text('print(\"not json\", flush=True)\\n' + p.read_text(encoding='utf-8'),"
        " encoding='utf-8')\n",
        encoding="utf-8",
    )
    ref = TASK / "solutions" / "reference"
    proc = _graded_run(tmp_path, "kept", ref, printer)
    assert proc.returncode == 0, proc.stdout
    # the same task with the redirect removed from worker.py: the print corrupts the channel
    broken = tmp_path / "broken_task"
    shutil.copytree(TASK, broken)
    worker = broken / "tests" / "worker.py"
    text = worker.read_text("utf-8")
    assert "    os.dup2(2, 1)\n" in text
    worker.write_text(text.replace("    os.dup2(2, 1)\n", ""), encoding="utf-8")
    app = fresh_app(broken, tmp_path / "broken_app")
    apply(ref, app)
    apply(printer, app)
    proc = run_verify_raw(broken, app)
    assert proc.returncode == 1
    assert set(json.loads(proc.stdout).values()) == {False}
