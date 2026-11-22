"""Repo-level guards for the RTL grader: one Playwright version, one base image."""

import hashlib
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PLAYWRIGHT_VERSION = "1.64.1"
BASE_IMAGE = (
    "mcr.microsoft.com/playwright/python:v1.64.1-noble"
    "@sha256:330d401ae23c905896a0c26c66c36fc971b621519e7b11b435a8328d7bf6e031"
)
RTL_WORKFLOW = ROOT / ".github" / "workflows" / "rtl-checks.yml"


def test_one_playwright_version_everywhere():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["dependency-groups"]["browser"] == [f"playwright=={PLAYWRIGHT_VERSION}"]
    assert not any("playwright" in d for d in pyproject["project"]["dependencies"])

    assert f"v{PLAYWRIGHT_VERSION}-noble@sha256:" in BASE_IMAGE

    for dockerfile in sorted(ROOT.glob("tasks/c-rtl-ui/*/environment/Dockerfile")):
        from_lines = re.findall(r"^FROM\s+(\S+)", dockerfile.read_text("utf-8"), re.MULTILINE)
        assert from_lines[-1] == BASE_IMAGE, f"{dockerfile}: final stage must be {BASE_IMAGE}"

    workflow = RTL_WORKFLOW.read_text(encoding="utf-8")
    images = re.findall(r"^\s+image:\s*(\S+)", workflow, re.MULTILINE)
    assert images == [BASE_IMAGE], f"{RTL_WORKFLOW}: container image must be {BASE_IMAGE}"


def test_physical_tailwind_classes():
    from kilmeh.graders.rtl_checks import physical_tailwind_classes

    physical = [
        "ml-4", "-ml-2", "mr-auto", "pl-2", "pr-[3px]", "md:pl-2", "hover:rtl:mr-1",
        "left-0", "-right-2", "right-1/2", "text-left", "text-right", "float-left",
        "clear-right", "rounded-l", "rounded-r-lg", "rounded-tl-md", "rounded-br",
        "border-l", "border-r-2", "border-l-red-500", "scroll-ml-4", "scroll-pr-2", "!ml-2",
        "[&:hover]:ml-2", "left-1/2", "right-full", "ml-0.5", "pl-px", "mr-(--gap)",
        "border-l-4", "border-l-[3px]", "rounded-l-full", "rounded-tr-2xl", "scroll-pl-2",
        "[margin-left:4px]", "md:[padding-right:2px]", "[float:left]", "[text-align:right]",
        "[border-left-color:red]", "rtl:ml-4", "group-hover:-ml-1",
    ]  # fmt: skip
    fine = [
        "ms-4", "me-2", "ps-2", "pe-1", "mx-4", "px-2", "my-1", "space-x-4", "start-0", "end-2",
        "inset-x-0", "text-start", "text-end", "text-center", "float-start", "clear-end",
        "rounded-s-lg", "rounded-e", "rounded-lg", "rounded-t-lg", "border-s", "border-e-2",
        "border-red-500", "border-t", "bg-right", "object-left", "flex", "ring", "md:ms-2",
        "scroll-ms-4", "left-nav", "right-column", "pr-card", "border-l-accent", "ml-foo",
        "ltr:ml-4", "md:ltr:pl-2", "[margin-inline-start:4px]", "[color:red]", "[left-nav]",
        "rounded-l-foo", "text-left-aligned", "float-left-x",
    ]  # fmt: skip
    assert physical_tailwind_classes(physical) == physical
    assert physical_tailwind_classes(fine) == []
    assert physical_tailwind_classes(physical + fine) == physical


# ---- RTL task harness guards (pure Python, default run) ----

CANONICAL = ROOT / "src" / "kilmeh" / "graders" / "rtl_checks.py"
RTL_TASKS = sorted(ROOT.glob("tasks/c-rtl-ui/*/task.toml"))
EXPECTED_RTL_TASKS = [
    "rtl-bidi-chat-feed",
    "rtl-bidi-data-cells",
    "rtl-bidi-name-slots",
    "rtl-contact-page-build",
    "rtl-nav-fix",
    "rtl-order-summary-fix",
    "rtl-react-chat",
    "rtl-tailwind-logical-convert",
    "rtl-tailwind-sidebar",
]

TEST_SH = (
    "#!/bin/bash\n"
    "mkdir -p /logs/verifier\n"
    "echo 0 > /logs/verifier/reward.txt\n"
    "cd /\n"
    "if bash /tests/build.sh /app /tmp/kilmeh-build > /logs/verifier/build.log 2>&1 \\\n"
    "  && python3 -I /tests/verify.py /app /tmp/kilmeh-build"
    " > /logs/verifier/checks.json 2> /logs/verifier/verify.log\n"
    "then echo 1 > /logs/verifier/reward.txt; fi\n"
)


def test_expected_rtl_tasks_exist():
    assert [p.parent.name for p in RTL_TASKS] == EXPECTED_RTL_TASKS


def test_vendored_rtl_checks_identical():
    assert RTL_TASKS, "no RTL tasks found"
    for toml in RTL_TASKS:
        vendored = toml.parent / "tests" / "rtl_checks.py"
        assert vendored.read_bytes() == CANONICAL.read_bytes(), (
            f"{vendored} drifted: cp src/kilmeh/graders/rtl_checks.py {toml.parent}/tests/"
        )


def test_rtl_tasks_share_test_sh():
    assert RTL_TASKS, "no RTL tasks found"
    for toml in RTL_TASKS:
        assert (toml.parent / "tests" / "test.sh").read_bytes() == TEST_SH.encode("utf-8"), toml


LEVANTINE_SHA256 = {
    "rtl-nav-fix": "5e385a11a114ed4047f8a5aee4dc4afa74d8dc5913686fd4bf82b8c6339d8058",
    "rtl-order-summary-fix": "a7b9dbd6b2e2c03a8d66b617a74c0f52f81fa1271007f51ec1a2f15f5b8ca467",
    "rtl-contact-page-build": "e33e8913b4de709d9108fd158f495aa8b520307e8e8ae2536d1df63662062bf1",
    "rtl-react-chat": "7b0793e88e66ff78f33ff876bbf0b0b96f57a08b5f1dea669cf44b8f3342f6a7",
    "rtl-tailwind-sidebar": "f3bf23482618759ed8bdc78401257480628f3745dda41cd0b5e9ccaf28ec9717",
    "rtl-tailwind-logical-convert": (
        "ed0392154cef9df8406dcf9e7cba82d9900cc3b6a006de05d55a6c312432f35b"
    ),
    # TODO(board) placeholders: the board writes these prompts, then their hashes go here
    "rtl-bidi-chat-feed": "af4a3217e60b57c3243d1f60bf6c5e8087e4d9d943a1f93e770fcd8ba561ab30",
    "rtl-bidi-name-slots": "af4a3217e60b57c3243d1f60bf6c5e8087e4d9d943a1f93e770fcd8ba561ab30",
    "rtl-bidi-data-cells": "af4a3217e60b57c3243d1f60bf6c5e8087e4d9d943a1f93e770fcd8ba561ab30",
}


def test_rtl_tasks_have_grader_files_spec_and_pinned_prompt():
    assert RTL_TASKS, "no RTL tasks found"
    for toml in RTL_TASKS:
        task = toml.parent
        for name in ("test.sh", "build.sh", "verify.py", "rtl_checks.py"):
            assert (task / "tests" / name).is_file(), f"{task}/tests/{name}"
        data = (task / "prompts" / "levantine.md").read_bytes()
        assert hashlib.sha256(data).hexdigest() == LEVANTINE_SHA256[task.name], task.name
        spec = (task / "fixture" / "SPEC.md").read_bytes()
        assert spec.startswith(b"# Requirements\n\n"), task.name
        if "tailwind" in task.name:
            assert (task / "fixture" / ".gitignore").read_bytes() == b"SPEC.md\n"
        assert (task / "REVIEW.md").is_file()


ARABIC_RUN = re.compile(r"[؀-ۿ]+")


def test_review_lists_every_arabic_string_in_the_fixture():
    assert RTL_TASKS, "no RTL tasks found"
    for toml in RTL_TASKS:
        task = toml.parent
        review = (task / "REVIEW.md").read_text("utf-8")
        assert "Fixture content for native review" in review
        paths = sorted((task / "fixture").rglob("*")) + sorted((task / "solutions").rglob("*.py"))
        paths += sorted((ROOT / "tests" / "rtl_alternatives" / task.name).glob("*.py"))
        paths += sorted((ROOT / "tests" / "rtl_gaming" / task.name).glob("*.py"))
        for path in paths:
            if path.suffix not in {".html", ".css", ".md", ".js", ".jsx", ".py"}:
                continue
            for word in ARABIC_RUN.findall(path.read_text("utf-8")):
                assert word in review, f"{path.name}: {word} missing from {task.name}/REVIEW.md"


def test_order_summary_name_sample_is_the_fixture_bytes():
    """The Arabic name typed by input_direction is copied from the fixture, never retyped."""
    import hashlib

    task = ROOT / "tasks/c-rtl-ui/rtl-order-summary-fix"
    html = (task / "fixture/index.html").read_text("utf-8")
    placeholder = re.search(r'data-testid="name"[^>]*placeholder="([^"]+)"', html).group(1)
    sample = (task / "tests/name_sample.txt").read_bytes()
    assert sample == placeholder.encode("utf-8")
    assert hashlib.sha256(sample).hexdigest() == ORDER_SUMMARY_NAME_SHA256


ORDER_SUMMARY_NAME_SHA256 = "eab04c822db42e5cf566e84cd76b0da71badfad630df13591c763280ed4e7dfd"


def _testid_text_digest(html: str) -> str:
    """sha256 of the whitespace-collapsed textContent of every [data-testid] element in document
    order, joined by newlines: the same value verify.py computes in the browser."""
    import hashlib
    from html.parser import HTMLParser

    void = {"meta", "link", "br", "img", "input", "hr"}

    class Collect(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.open: list[list[str] | None] = []  # one slot per open element
            self.elements: list[list[str]] = []  # the data-testid ones, in document order

        def handle_starttag(self, tag, attrs):
            if tag in void:
                return
            bucket = [] if any(name == "data-testid" for name, _ in attrs) else None
            if bucket is not None:
                self.elements.append(bucket)
            self.open.append(bucket)

        def handle_endtag(self, tag):
            if tag not in void and self.open:
                self.open.pop()

        def handle_data(self, data):
            for bucket in self.open:
                if bucket is not None:
                    bucket.append(data)

    parser = Collect()
    parser.feed(html)
    texts = [re.sub(r"\s+", " ", "".join(parts)).strip() for parts in parser.elements]
    return hashlib.sha256("\n".join(texts).encode("utf-8")).hexdigest()


def test_tailwind_sidebar_text_digest_matches_the_fixture():
    """verify.py pins the text of the data-testid elements; a fixture edit must update it."""
    task = ROOT / "tasks/c-rtl-ui/rtl-tailwind-sidebar"
    pinned = re.search(
        r'^TEXT_DIGEST = "([0-9a-f]{64})"', (task / "tests/verify.py").read_text("utf-8"), re.M
    )
    assert pinned, "TEXT_DIGEST missing in verify.py"
    digest = _testid_text_digest((task / "fixture/index.html").read_text("utf-8"))
    assert digest == pinned.group(1)


def test_logical_convert_pristine_copy_is_the_fixture():
    """verify.py renders tests/pristine as the expected layout: it must be the fixture's bytes."""
    task = ROOT / "tasks/c-rtl-ui/rtl-tailwind-logical-convert"
    names = ["index.html", "notifications.html", "billing.html", "src/input.css"]
    pristine = sorted(
        p.relative_to(task / "tests/pristine").as_posix()
        for p in (task / "tests/pristine").rglob("*")
        if p.is_file()
    )
    assert pristine == sorted(names)
    for name in names:
        assert (task / "tests/pristine" / name).read_bytes() == (
            task / "fixture" / name
        ).read_bytes()


# ---- pip hashes in the task images ----

PIP_PACKAGES = ["playwright", "pyee", "greenlet", "typing-extensions"]
PIN = re.compile(r"([A-Za-z0-9_.-]+)==(\S+)((?: --hash=sha256:[0-9a-f]{64})+)")


def lock_pins() -> dict[str, tuple[str, set[str]]]:
    """name -> (version, sha256 of every linux amd64 and arm64 wheel for CPython 3.12, plus
    pure-Python wheels), straight from uv.lock."""
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    pins = {}
    for pkg in lock["package"]:
        if pkg["name"] not in PIP_PACKAGES:
            continue
        hashes = set()
        for wheel in pkg["wheels"]:
            name = wheel["url"].rsplit("/", 1)[1]
            linux = re.search(r"manylinux.*(x86_64|aarch64)\.whl$", name) and (
                "-py3-none-" in name or "-cp312-cp312-" in name
            )
            if linux or name.endswith("-none-any.whl"):
                hashes.add(wheel["hash"].removeprefix("sha256:"))
        pins[pkg["name"]] = (pkg["version"], hashes)
    return pins


def pip_block(dockerfile: Path) -> str:
    text = dockerfile.read_text(encoding="utf-8")
    match = re.search(r"^RUN printf .*?rm /tmp/req\.txt\n", text, re.MULTILINE | re.DOTALL)
    assert match, f"{dockerfile}: no hash-pinned pip RUN block"
    return match.group(0)


def test_rtl_dockerfiles_pip_hashes_match_uv_lock():
    assert RTL_TASKS, "no RTL tasks found"
    pins = lock_pins()
    assert sorted(pins) == sorted(PIP_PACKAGES)
    blocks = set()
    for toml in RTL_TASKS:
        block = pip_block(toml.parent / "environment" / "Dockerfile")
        blocks.add(block)
        assert "--require-hashes" in block and "--no-deps" in block
        found = {
            m[1]: (m[2], set(re.findall(r"sha256:([0-9a-f]{64})", m[3])))
            for m in PIN.finditer(block)
        }
        assert found == pins, f"{toml.parent.name}: Dockerfile pins differ from uv.lock"
    assert len(blocks) == 1, "every RTL task must use the same pip block"


def test_contact_page_name_sample_is_a_byte_copy():
    """The contact task reuses the order-summary task's Arabic name bytes, never retyped."""
    import hashlib

    sample = (ROOT / "tasks/c-rtl-ui/rtl-contact-page-build/tests/name_sample.txt").read_bytes()
    original = (ROOT / "tasks/c-rtl-ui/rtl-order-summary-fix/tests/name_sample.txt").read_bytes()
    assert sample == original
    assert hashlib.sha256(sample).hexdigest() == ORDER_SUMMARY_NAME_SHA256


def test_rtl_workflow_runs_the_docker_task_tests_on_rtl_paths_only():
    workflow = RTL_WORKFLOW.read_text(encoding="utf-8")
    assert "  rtl-tasks:" in workflow, "missing the rtl-tasks job"
    job = workflow[workflow.index("  rtl-tasks:") :]
    assert "uv run pytest -m docker tests/test_rtl_tasks.py" in job
    assert re.search(r"timeout-minutes: \d+", job), "the RTL task job needs its own time limit"
    assert "container:" not in job, "docker tests need the host's Docker, not a container job"
    # path-filtered on both triggers, so the heavy jobs never run for unrelated changes
    assert workflow.count('"tasks/c-rtl-ui/**"') == 2
    assert workflow.count('"tests/rtl_*/**"') == 2
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    selftest = ci[ci.index("  task-selftest:") :]
    assert "timeout-minutes: 15" in selftest


# ---- rtl-react-chat: the Arabic sample and the npm and node pins ----

REACT_TASK = ROOT / "tasks/c-rtl-ui/rtl-react-chat"
COMPOSER_SAMPLE_SHA256 = "e26b5fd95bd4c5606daf3770cfbd4e6d026345f3e5c7fa21de3fd5bd965f7acb"


def test_react_chat_composer_sample_is_the_fixture_bytes():
    """The Arabic typed into the composer is copied from the fixture, never retyped."""
    import hashlib

    jsx = (REACT_TASK / "fixture/src/Chat.jsx").read_text("utf-8")
    placeholder = re.search(r'data-testid="composer" placeholder="([^"]+)"', jsx).group(1)
    sample = (REACT_TASK / "tests/composer_sample.txt").read_bytes()
    assert sample == placeholder.encode("utf-8")
    assert hashlib.sha256(sample).hexdigest() == COMPOSER_SAMPLE_SHA256


def test_react_chat_npm_and_node_are_pinned():
    import json

    pkg = json.loads((REACT_TASK / "fixture/package.json").read_text("utf-8"))
    wanted = {**pkg["dependencies"], **pkg["devDependencies"]}
    assert sorted(wanted) == ["esbuild", "react", "react-dom"]
    assert all(re.fullmatch(r"\d+\.\d+\.\d+", v) for v in wanted.values()), "exact versions only"
    lock = json.loads((REACT_TASK / "fixture/package-lock.json").read_text("utf-8"))
    packages = lock["packages"]
    for name, version in wanted.items():
        assert packages[f"node_modules/{name}"]["version"] == version
    for entry in packages.values():
        if entry.get("resolved"):
            assert entry["resolved"].startswith("https://registry.npmjs.org/")
            assert entry["integrity"].startswith("sha512-")
    # esbuild's per-platform binary must be in the lock for both image architectures
    for arch in ("linux-x64", "linux-arm64"):
        assert packages[f"node_modules/@esbuild/{arch}"]["version"] == wanted["esbuild"]

    dockerfile = (REACT_TASK / "environment/Dockerfile").read_text("utf-8")
    assert re.search(
        r"^FROM node:\d+\.\d+\.\d+-bookworm-slim@sha256:[0-9a-f]{64} AS deps$",
        dockerfile,
        re.MULTILINE,
    )
    assert "RUN npm ci --ignore-scripts" in dockerfile


def test_chat_feed_arabic_words_come_from_the_fixture():
    """verify.py reads Arabic words from tests/arabic_words.json: each must be in its message."""
    task = ROOT / "tasks/c-rtl-ui/rtl-bidi-chat-feed"
    html = (task / "fixture/index.html").read_text("utf-8")
    texts = dict(re.findall(r'data-testid="(m[0-9])">.*?<p class="text">(.*?)</p>', html))
    words = json.loads((task / "tests/arabic_words.json").read_text("utf-8"))
    assert sorted(words) == sorted(texts)
    for msg, pair in words.items():
        assert len(pair) == 2 and all(ARABIC_RUN.fullmatch(w) for w in pair), msg
        assert texts[msg].index(pair[0]) < texts[msg].index(pair[1], texts[msg].index(pair[0]) + 1)


def test_bidi_pristine_copies_are_the_fixture():
    """The bidi tasks grade text against tests/pristine_index.html: it must be the fixture."""
    for name in ("rtl-bidi-chat-feed", "rtl-bidi-name-slots", "rtl-bidi-data-cells"):
        task = ROOT / "tasks/c-rtl-ui" / name
        pristine = (task / "tests/pristine_index.html").read_bytes()
        assert pristine == (task / "fixture/index.html").read_bytes(), name
