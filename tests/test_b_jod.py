"""Grader tests for jod-currency-format (Track B, JavaScript on Node 22, runs the agent's money.js).

Host tests run tests/verify.mjs against a temp copy of the fixture (KILMEH_APP), like the other
Track B graders. They need Linux (`process.geteuid`) and `node` on PATH, and skip without node.
Each check fails under its own mutation of the reference solution; the dependent checks that fail
with it are pinned exactly. Docker-marked cases run the real test.sh as root in the pinned image.
"""

import hashlib
import re
import shutil

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

pytestmark_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

TASK = task_dir("jod-currency-format")
REFERENCE = TASK / "solutions" / "reference"
KNOWN_BAD = TASK / "solutions" / "known-bad"
ALTERNATIVES = ROOT / "tests" / "b_alternatives" / "jod-currency-format"

CHECKS = [
    "en_format",
    "ar_format",
    "ar_arab_format",
    "three_decimals_hidden",
    "negative",
    "zero",
    "bigint_large",
    "rejects_non_integer",
    "receipt_works",
]
FIXTURE_SHA256 = {
    "package.json": "30d57a6b83876482804e6ddf4eee8df5eb74e4aac09751b5759952d73378a317",
    "README.md": "d51b809edb3774f4a5025f9336b0403478abe1a466976256eb7358c610aebbc1",
    "examples.mjs": "fa8bb62d77888d0dbeafba0f4ab55aa4c4ef8b433db5a31a33ecc9fd5a856295",
    "src/money.js": "5e2ea8a25a064be0a3f8d1ab670242b87a03a2f88293103e4b98220a32c5be4d",
    "src/receipt.js": "b79d04de1f5d1f75b7922ce689b1441e28152693fe69a1b55f3858c1dd204f7b",
    "SPEC.md": "17898f04fdbf31a9187acbe0b84d4ba272325b6fdbd818336a41a6129afc6f28",
}
PROMPT_SHA256 = {
    "en.md": "d28a2c7680f38e322de982a887d29a06257f34c7f378c4b3f7c5c14d8aa73330",
    "levantine.md": "759d08a08d67440fedd3081e776128ce3876c94e9de1b2e06b96cba7c2d13e52",
}
FROM_LINE = (
    "FROM node:22.23.5-bookworm-slim"
    "@sha256:e9f565d32859f0cbfb52125eafe8be39390f24dac302dc3cdf566e8ba3ab21ee"
)

# The two-decimal habit and the stub fail everything (the stub throws a plain Error).
KNOWN_BAD_FAILS = set(CHECKS)
UNTOUCHED_FAILS = set(CHECKS)

# check -> (file in the app, text in the reference, replacement, exact failing set). Each
# replacement reintroduces one defect; dependent checks that fail with it are pinned.
MONEY = "src/money.js"
MUTATIONS = {
    "en_format": (
        MONEY,
        "? `${sign}JD ${number}`",
        "? `${sign}JD\\u00a0${number}`",
        {"bigint_large", "en_format", "negative", "receipt_works", "three_decimals_hidden", "zero"},
    ),
    "ar_format": (
        MONEY,
        ": `${sign}${number} JD`",
        ": `${sign}${number}JD`",
        {
            "ar_arab_format",
            "ar_format",
            "bigint_large",
            "negative",
            "receipt_works",
            "three_decimals_hidden",
            "zero",
        },
    ),
    "ar_arab_format": (
        MONEY,
        'c === "." ? "\\u066b"',
        'c === "." ? "."',
        {
            "ar_arab_format",
            "bigint_large",
            "negative",
            "receipt_works",
            "three_decimals_hidden",
            "zero",
        },
    ),
    "three_decimals_hidden": (
        MONEY,
        'String(n % 1000n).padStart(3, "0")',
        'String(n % 1000n).padStart(3, "0").replace(/^(\\d\\d)0$/, "$1")',
        {
            "ar_arab_format",
            "ar_format",
            "bigint_large",
            "en_format",
            "negative",
            "receipt_works",
            "three_decimals_hidden",
            "zero",
        },
    ),
    "negative": (
        MONEY,
        'const sign = n < 0n ? "-" : "";',
        'const sign = n < 0n ? "\\u2212" : "";',
        {"bigint_large", "negative", "three_decimals_hidden"},
    ),
    "zero": (
        MONEY,
        'const sign = n < 0n ? "-" : "";',
        'const sign = n < 0n || Object.is(fils, -0) ? "-" : "";',
        {"zero"},
    ),
    "bigint_large": (
        MONEY,
        'if (typeof fils === "bigint") n = fils;',
        'if (typeof fils === "bigint") n = BigInt(Number(fils));',
        {"bigint_large"},
    ),
    "rejects_non_integer": (
        MONEY,
        "Number.isSafeInteger(fils)",
        "Number.isInteger(fils)",
        {"rejects_non_integer"},
    ),
    "receipt_works": (
        "src/receipt.js",
        "`Total: ",
        "`Sum: ",
        {"receipt_works"},
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


def test_sources_are_ascii_with_arabic_as_escapes():
    for path in [*TASK.rglob("*.js"), *TASK.rglob("*.mjs"), *TASK.rglob("*.sh")]:
        path.read_bytes().decode("ascii")


def test_prompt_states_the_graded_rules():
    text = (TASK / "fixture" / "SPEC.md").read_text("utf-8")
    for needle in ("Intl", "RangeError", "JD 1,234.500", "1,234.500 JD", "U+066C", "U+066B"):
        assert needle in text, needle


def test_dockerfile_copies_only_the_fixture_and_pins_the_image():
    lines = (TASK / "environment" / "Dockerfile").read_text("utf-8").splitlines()
    assert lines == [FROM_LINE, "WORKDIR /app", "COPY fixture/ /app/"]
    assert re.fullmatch(r"FROM node:22\.\d+\.\d+-bookworm-slim@sha256:[0-9a-f]{64}", lines[0])


def test_test_sh_order_and_hardening():
    lines = (TASK / "tests" / "test.sh").read_text("utf-8").splitlines()
    zero = lines.index("echo 0 > /logs/verifier/reward.txt")
    readable = lines.index("chmod -R a+rX /app")
    lock = lines.index("if ! chown -R 0:0 /tests || ! chmod -R go-rwx /tests; then")
    verify = next(i for i, ln in enumerate(lines) if "/tests/verify.mjs" in ln)
    assert zero < readable < lock < verify
    assert "node /tests/verify.mjs" in lines[verify]


@pytestmark_node
def test_reference_passes(app):
    apply(REFERENCE, app)
    rc, result = run_verify(TASK, app)
    assert list(result) == CHECKS
    assert failing(result) == set()
    assert rc == 0


@pytestmark_node
def test_reference_passes_on_repeated_random_data(app):
    apply(REFERENCE, app)
    for _ in range(5):
        assert run_verify(TASK, app) == (0, dict.fromkeys(CHECKS, True))


@pytestmark_node
def test_known_bad_fails(app):
    apply(KNOWN_BAD, app)
    rc, result = run_verify(TASK, app)
    assert failing(result) == KNOWN_BAD_FAILS
    assert rc == 1


@pytestmark_node
def test_untouched_fixture_fails(app):
    rc, result = run_verify(TASK, app)
    assert failing(result) == UNTOUCHED_FAILS
    assert rc == 1


@pytestmark_node
def test_reference_logs_a_pass_line_per_check(app):
    apply(REFERENCE, app)
    proc = run_verify_raw(TASK, app)
    assert check_lines(proc.stderr) == [("PASS", k) for k in CHECKS]


@pytestmark_node
def test_known_bad_logs_fail_lines_without_leaking_values(app):
    apply(KNOWN_BAD, app)
    proc = run_verify_raw(TASK, app)
    lines = check_lines(proc.stderr)
    assert [k for _, k in lines] == CHECKS
    assert {k for v, k in lines if v == "FAIL"} == KNOWN_BAD_FAILS


@pytestmark_node
def test_world_readable_tests_dir_is_refused(app):
    apply(REFERENCE, app)
    proc = run_verify_raw(TASK, app, lock=False)
    assert proc.returncode == 2
    assert "refusing to grade" in proc.stderr


def test_one_mutation_per_check():
    assert list(MUTATIONS) == CHECKS


@pytestmark_node
@pytest.mark.parametrize("check", CHECKS)
def test_each_check_fails_in_isolation(app, check):
    apply(REFERENCE, app)
    name, old, new, expected = MUTATIONS[check]
    path = app / name
    source = path.read_text("utf-8")
    assert source.count(old) == 1, "mutation target must match once"
    path.write_text(source.replace(old, new), "utf-8", newline="\n")
    rc, result = run_verify(TASK, app)
    assert check in failing(result)
    assert failing(result) == expected
    assert rc == 1


@pytestmark_node
def test_intl_alternative_scores_0_because_the_spec_is_not_cldr(app):
    """QA alternative (a): Intl gives `JOD 1,234.500` and a CLDR Arabic layout, never the spec."""
    (app / "src" / "money.js").write_bytes((ALTERNATIVES / "intl.js").read_bytes())
    rc, result = run_verify(TASK, app)
    assert failing(result) == set(CHECKS)
    assert rc == 1


GAMING = {
    # Forge a result file on fd 3 and quit: the worker's own write replaces it, or the parent
    # finds a malformed or wrong-length list.
    "forge_fd3_and_exit": (
        'import fs from "node:fs";\n'
        'fs.writeSync(3, JSON.stringify([["ok", "string", "JD 0.000"]]));\n'
        "process.exit(0);\n"
    ),
    "exit_at_import": "process.exit(0);\n",
    "fake_json_on_stdout": "console.log(JSON.stringify({ en_format: true }));\nprocess.exit(0);\n",
    "hard_coded_examples": (
        "export function formatJOD(fils, locale) {\n"
        '  if (fils === 1234500) return locale === "en-JO" ? "JD 1,234.500" : "1,234.500 JD";\n'
        '  if (fils === 5) return "JD 0.005";\n'
        '  throw new RangeError("no");\n}\n'
    ),
    "float_path": (
        "export function formatJOD(fils, locale) {\n"
        "  const n = Number(fils);\n"
        '  if (!Number.isFinite(n) || n % 1 !== 0) throw new RangeError("no");\n'
        '  const t = (Math.abs(n) / 1000).toFixed(3).replace(/\\B(?=(\\d{3})+\\b)/g, ",");\n'
        '  const s = n < 0 ? "-" : "";\n'
        '  return locale === "en-JO" ? `${s}JD ${t}` : `${s}${t} JD`;\n}\n'
    ),
}


@pytestmark_node
@pytest.mark.parametrize("name", list(GAMING))
def test_gaming_scores_0(app, name):
    (app / "src" / "money.js").write_text(GAMING[name], "utf-8", newline="\n")
    rc, result = run_verify(TASK, app)
    assert rc == 1
    # The float path is right on small amounts, so en_format may pass; it must lose the rest.
    assert failing(result) >= {"bigint_large", "three_decimals_hidden"}


@pytestmark_node
def test_agent_stdout_and_stderr_are_discarded(app):
    apply(REFERENCE, app)
    path = app / "src" / "money.js"
    noisy = 'console.log("PASS en_format"); console.error("noise");\n' + path.read_text("utf-8")
    path.write_text(noisy, "utf-8", newline="\n")
    assert run_verify(TASK, app) == (0, dict.fromkeys(CHECKS, True))


@pytestmark_node
def test_node_modules_cannot_shadow_node_builtins(app):
    """The worker only imports `node:` builtins and file URLs, so a planted package named like
    a builtin is never loaded."""
    apply(REFERENCE, app)
    shadow = app / "node_modules" / "fs"
    shadow.mkdir(parents=True)
    (shadow / "index.js").write_text('throw new Error("shadowed");\n', "utf-8")
    (shadow / "package.json").write_text('{"name": "fs", "main": "index.js"}\n', "utf-8")
    assert run_verify(TASK, app) == (0, dict.fromkeys(CHECKS, True))


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
case_run planted_reward "bash /solutions/known-bad/solve.sh" \
  "mkdir -p /logs/verifier && echo 1 > /logs/verifier/reward.txt"
case_run intl "cp /alt/intl.js /app/src/money.js"
case_run intl_decimal "cp /alt/intl_decimal.js /app/src/money.js"
case_run nobody_daemon "bash /solutions/reference/solve.sh" "node /extra/nobody_daemon.mjs"
"""

NOBODY_DAEMON = """import { spawn } from "node:child_process";

const child = spawn(
  process.execPath,
  ["-e", "setTimeout(() => {}, 600000)"],
  { detached: true, stdio: "ignore", uid: 65534, gid: 65534 },
);
child.unref();
"""


@pytest.fixture(scope="module")
def image_cases(tmp_path_factory):
    extra = tmp_path_factory.mktemp("extra")
    (extra / "nobody_daemon.mjs").write_text(NOBODY_DAEMON, encoding="utf-8")
    mounts = {TASK / "solutions": "/solutions", extra: "/extra", ALTERNATIVES: "/alt"}
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
    assert image_cases["planted_reward"]["reward"] == "0"


@pytest.mark.docker
def test_in_image_intl_alternative_scores_0(image_cases):
    """Pinned image (ICU 78.3): Intl prints `JOD 1,234.500` and CLDR Arabic, never the spec."""
    assert image_cases["intl"]["reward"] == "0"


@pytest.mark.docker
def test_in_image_intl_decimal_alternative_scores_1(image_cases):
    """Grading is output-only: Intl `decimal` style plus a hand-written `JD` is a valid method."""
    assert image_cases["intl_decimal"]["reward"] == "1"


@pytest.mark.docker
def test_in_image_uid_65534_daemon_is_swept_and_reference_still_scores_1(image_cases):
    case = image_cases["nobody_daemon"]
    assert case["alive"] == "no", "the daemon outlived the grader"
    assert case["reward"] == "1"
