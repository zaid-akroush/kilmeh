"""Grader tests for arabic-file-io (Track B, runs the agent's ingest.py on fresh inputs).

Host tests run tests/verify.py against a temp copy of the fixture (KILMEH_APP), like the other
Track B graders; they need Linux (`os.geteuid`), so run them in the python:3.12 image. Each check
fails under its own mutation of the reference solution; the dependent checks that fail with it
are pinned exactly.
"""

import ast
import hashlib
import re
import time

import pytest

from b_helpers import (
    apply,
    check_lines,
    failing,
    fresh_app,
    run_in_image,
    run_verify,
    run_verify_raw,
    task_dir,
)

TASK = task_dir("arabic-file-io")
REFERENCE = TASK / "solutions" / "reference"

CHECKS = [
    "runs_ok",
    "csv_header_clean",
    "csv_utf8_values",
    "legacy_cp1256_decoded",
    "json_values_exact",
    "json_not_escaped",
    "no_bom_in_outputs",
    "doc_filenames_arabic",
    "doc_contents_exact",
]
FIXTURE_SHA256 = {
    "ingest.py": "1556e2f5a2ba33ed491320fc374d8b6c48bd1f444d35b14d6baeddbf9954ad76",
    "README.md": "193c1ca48964b267a974dd8600ba271bfe238d27596bb322eb1548d414bb461d",
    "sample/config.json": "48768809ce5505191875dbd30aac9a922563a14c6af46fb4f95db2d2c1ba7634",
    "sample/legacy.csv": "61b6f949cb2015db9f4c52f4b5352a224f3ef45b5b64aa84827889d76771cf2c",
    "sample/products.csv": "76bf29995eb2af3ce85f77a51483670ce357eb011554f98bc0553155250166b8",
    "sample/docs/تقرير_المبيعات.txt": (
        "4917eadfd5e71ae8fea9d02514e3710b9a303c87fca04b7700a6e7479c6c423d"
    ),
    "SPEC.md": "431511b50b43cdfb06a8847f611d5278645da206ba5622d973d5fb982ab3da50",
}
PROMPT_SHA256 = {
    "en.md": "6811816084e472076ea666084a0abbb302261ac2a5d660306dccbcccac804908",
    "levantine.md": "495bf848a069710d040d90ea55b1e5d06a6984e2b9db61573f1fa38dc80911ff",
}
FROM_LINE = (
    "FROM python:3.12.15-slim-bookworm"
    "@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70"
)

KNOWN_BAD_FAILS = {"legacy_cp1256_decoded", "json_not_escaped"}
UNTOUCHED_FAILS = {
    "csv_header_clean",
    "legacy_cp1256_decoded",
    "json_not_escaped",
    "doc_filenames_arabic",
    "doc_contents_exact",
}

# check -> (text in the reference ingest.py, replacement, exact failing set). The replacement
# reintroduces one defect; where the defect also breaks a dependent check, that one is pinned.
MUTATIONS = {
    "runs_ok": (
        "    main(sys.argv[1], sys.argv[2])",
        "    main(sys.argv[1], sys.argv[2])\n    sys.exit(1)",
        {"runs_ok"},
    ),
    "csv_header_clean": ('"utf-8-sig")', '"utf-8")', {"csv_header_clean"}),
    "csv_utf8_values": (
        "    legacy = read_csv(",
        '    for r in products:\n        r["city"] = r["city"][::-1]\n    legacy = read_csv(',
        {"csv_utf8_values"},
    ),
    "legacy_cp1256_decoded": ('"cp1256")', '"latin-1")', {"legacy_cp1256_decoded"}),
    "json_values_exact": (
        '"title": config["title"]',
        '"title": config["title"][::-1]',
        {"json_values_exact"},
    ),
    "json_not_escaped": (
        "indent=2, ensure_ascii=False",
        "indent=2, ensure_ascii=True",
        {"json_not_escaped"},
    ),
    "no_bom_in_outputs": (
        '"summary.json"), "w", encoding="utf-8")',
        '"summary.json"), "w", encoding="utf-8-sig")',
        {"no_bom_in_outputs"},
    ),
    "doc_filenames_arabic": (
        'stem + ".summary.txt"',
        'stem.encode("ascii", "ignore").decode() + ".summary.txt"',
        {"doc_filenames_arabic", "doc_contents_exact"},
    ),
    "doc_contents_exact": (
        'f.write(first_line + "\\n")',
        'f.write(first_line[:-1] + "\\n")',
        {"doc_contents_exact"},
    ),
}


@pytest.fixture
def app(tmp_path):
    return fresh_app(TASK, tmp_path)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_fixture_files_are_pinned():
    root = TASK / "fixture"
    files = {p.relative_to(root).as_posix(): p for p in root.rglob("*") if p.is_file()}
    assert set(files) == set(FIXTURE_SHA256)
    for name, expected in FIXTURE_SHA256.items():
        assert sha256(files[name].read_bytes()) == expected, name


def test_prompts_are_pinned():
    for name, expected in PROMPT_SHA256.items():
        assert sha256((TASK / "prompts" / name).read_bytes()) == expected, name


def test_dockerfile_copies_only_the_fixture_and_pins_the_image():
    lines = (TASK / "environment" / "Dockerfile").read_text("utf-8").splitlines()
    assert lines == [FROM_LINE, "WORKDIR /app", "COPY fixture/ /app/"]
    assert re.fullmatch(r"FROM python:3\.12\.\d+-slim-bookworm@sha256:[0-9a-f]{64}", lines[0])


def test_word_pools_are_windows_1256_encodable_where_needed():
    """Product names go into legacy.csv as cp1256: a name outside it would crash the grader."""
    tree = ast.parse((TASK / "tests" / "verify.py").read_text("utf-8"))
    pools = {
        t.id: ast.literal_eval(n.value)
        for n in tree.body
        if isinstance(n, ast.Assign)
        for t in n.targets
        if isinstance(t, ast.Name) and t.id.isupper() and isinstance(n.value, ast.List)
    }
    assert len(pools["PRODUCTS"]) >= 4
    for name in pools["PRODUCTS"]:
        name.encode("windows-1256")
    for pool in ("PRODUCTS", "CITIES", "TITLES", "DOC_FIRST", "DOC_SECOND", "SENTENCES"):
        assert len(set(pools[pool])) == len(pools[pool])


def test_test_sh_order_and_hardening():
    lines = (TASK / "tests" / "test.sh").read_text("utf-8").splitlines()
    zero = lines.index("echo 0 > /logs/verifier/reward.txt")
    readable = lines.index("chmod -R a+rX /app")
    lock = lines.index("if ! chown -R 0:0 /tests || ! chmod -R go-rwx /tests; then")
    verify = next(i for i, ln in enumerate(lines) if "/tests/verify.py" in ln)
    assert zero < readable < lock < verify
    assert "python3 -B -I -S /tests/verify.py" in lines[verify]


def test_reference_passes(app):
    apply(REFERENCE, app)
    rc, result = run_verify(TASK, app)
    assert list(result) == CHECKS
    assert failing(result) == set()
    assert rc == 0


def test_reference_passes_on_repeated_random_data(app):
    apply(REFERENCE, app)
    for _ in range(5):
        assert run_verify(TASK, app) == (0, dict.fromkeys(CHECKS, True))


def test_known_bad_fails(app):
    apply(TASK / "solutions" / "known-bad", app)
    rc, result = run_verify(TASK, app)
    assert failing(result) == KNOWN_BAD_FAILS
    assert rc == 1


def test_untouched_fixture_fails(app):
    rc, result = run_verify(TASK, app)
    assert failing(result) == UNTOUCHED_FAILS
    assert rc == 1


def test_reference_logs_a_pass_line_per_check(app):
    apply(REFERENCE, app)
    proc = run_verify_raw(TASK, app)
    assert check_lines(proc.stderr) == [("PASS", k) for k in CHECKS]


def test_known_bad_logs_fail_lines_without_leaking_values(app):
    apply(TASK / "solutions" / "known-bad", app)
    proc = run_verify_raw(TASK, app)
    lines = check_lines(proc.stderr)
    assert [k for _, k in lines] == CHECKS
    assert {k for v, k in lines if v == "FAIL"} == KNOWN_BAD_FAILS
    assert not re.search(r"[؀-ۿ]", proc.stderr), "Arabic text leaked into verify.log"


def test_one_mutation_per_check():
    assert list(MUTATIONS) == CHECKS


@pytest.mark.parametrize("check", CHECKS)
def test_each_check_fails_in_isolation(app, check):
    apply(REFERENCE, app)
    old, new, expected = MUTATIONS[check]
    source = (app / "ingest.py").read_text("utf-8")
    assert source.count(old) == 1, "mutation target must match once"
    (app / "ingest.py").write_text(source.replace(old, new), "utf-8", newline="\n")
    rc, result = run_verify(TASK, app)
    assert check in failing(result)
    assert failing(result) == expected
    assert rc == 1


@pytest.mark.parametrize(
    "old",
    [
        'open(os.path.join(in_dir, "config.json"), encoding="utf-8")',
        'open(os.path.join(docs_in, name), encoding="utf-8")',
    ],
)
def test_text_open_without_encoding_fails(app, old):
    """The grader turns EncodingWarning into an error, so a locale-default open() scores 0:
    it crashes before summary.json is written, so every check fails."""
    apply(REFERENCE, app)
    source = (app / "ingest.py").read_text("utf-8")
    assert source.count(old) == 1
    bare = old.replace(', encoding="utf-8"', "")
    (app / "ingest.py").write_text(source.replace(old, bare), "utf-8", newline="\n")
    rc, result = run_verify(TASK, app)
    assert failing(result) == set(CHECKS)
    assert rc == 1


def test_symlinked_summary_scores_0_on_its_checks(app):
    """A link out of the output directory is not followed."""
    apply(REFERENCE, app)
    source = (app / "ingest.py").read_text("utf-8")
    link = 'os.remove(os.path.join(out_dir, "summary.json"))\n    os.symlink("/etc/hostname", '
    source = source.replace(
        "json.dump(summary, f, indent=2, ensure_ascii=False)\n",
        "json.dump(summary, f, indent=2, ensure_ascii=False)\n    "
        + link
        + 'os.path.join(out_dir, "summary.json"))\n',
    )
    (app / "ingest.py").write_text(source, "utf-8", newline="\n")
    rc, result = run_verify(TASK, app)
    assert failing(result) == set(CHECKS) - {
        "runs_ok",
        "doc_filenames_arabic",
        "doc_contents_exact",
    }
    assert rc == 1


AFTER_DUMP = "json.dump(summary, f, indent=2, ensure_ascii=False)\n"


def mutate_after_dump(app, code):
    """Insert `code` (4-space indented) right after summary.json is written."""
    apply(REFERENCE, app)
    source = (app / "ingest.py").read_text("utf-8")
    assert source.count(AFTER_DUMP) == 1
    mutated = source.replace(AFTER_DUMP, AFTER_DUMP + code)
    (app / "ingest.py").write_text(mutated, "utf-8", newline="\n")


def test_bom_in_a_doc_output_fails_no_bom_in_outputs(app):
    apply(REFERENCE, app)
    old = 'stem + ".summary.txt"), "w", encoding="utf-8")'
    source = (app / "ingest.py").read_text("utf-8")
    assert source.count(old) == 1
    new = old.replace('"utf-8")', '"utf-8-sig")')
    (app / "ingest.py").write_text(source.replace(old, new), "utf-8", newline="\n")
    rc, result = run_verify(TASK, app)
    assert failing(result) == {"no_bom_in_outputs"}
    assert rc == 1


def test_escaped_title_with_raw_names_fails_json_not_escaped(app):
    """Names stay raw UTF-8; only the title is escaped. Guards the backslash-u clause."""
    code = (
        '    path = os.path.join(out_dir, "summary.json")\n'
        '    with open(path, encoding="utf-8") as f:\n'
        "        text = f.read()\n"
        '    escaped = config["title"].encode("unicode_escape").decode("ascii")\n'
        '    with open(path, "w", encoding="utf-8") as f:\n'
        '        f.write(text.replace(config["title"], escaped))\n'
    )
    mutate_after_dump(app, code)
    rc, result = run_verify(TASK, app)
    assert failing(result) == {"json_not_escaped"}
    assert rc == 1


def test_fifo_summary_scores_0_quickly(app):
    """A FIFO at summary.json is not opened blocking (O_NONBLOCK in read_regular)."""
    code = '    p = os.path.join(out_dir, "summary.json")\n    os.remove(p)\n    os.mkfifo(p)\n'
    mutate_after_dump(app, code)
    start = time.monotonic()
    rc, result = run_verify(TASK, app)
    assert time.monotonic() - start < 20
    assert failing(result) == set(CHECKS) - {
        "runs_ok",
        "doc_filenames_arabic",
        "doc_contents_exact",
    }
    assert rc == 1


# In-image cases: one container, each case on a fresh copy of /app, graded by the real test.sh
# as root with the network off (uid drop, sweep and reward.txt included).
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
  echo "CASE|$name|$reward|$alive"
}
case_run reference "bash /solutions/reference/solve.sh"
case_run known_bad "bash /solutions/known-bad/solve.sh"
case_run untouched
case_run nobody_daemon "bash /solutions/reference/solve.sh" "python3 /extra/nobody_daemon.py"
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
    (extra / "nobody_daemon.py").write_text(NOBODY_DAEMON, encoding="utf-8")
    mounts = {TASK / "solutions": "/solutions", extra: "/extra"}
    out = run_in_image(TASK, IMAGE_SCRIPT, mounts)
    cases = {}
    for line in out.splitlines():
        if line.startswith("CASE|"):
            _, name, reward, alive = line.split("|")
            cases[name] = {"reward": reward, "alive": alive}
    return cases


@pytest.mark.docker
def test_in_image_scores(image_cases):
    assert image_cases["reference"]["reward"] == "1"
    assert image_cases["known_bad"]["reward"] == "0"
    assert image_cases["untouched"]["reward"] == "0"


@pytest.mark.docker
def test_in_image_uid_65534_daemon_is_swept_and_reference_still_scores_1(image_cases):
    case = image_cases["nobody_daemon"]
    assert case["alive"] == "no", "the daemon outlived the grader"
    assert case["reward"] == "1"
