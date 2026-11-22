import re
import shutil
from pathlib import Path

import pytest

from kilmeh.cli import main
from kilmeh.tasks import validate_paths, validate_task_dir
from kilmeh.tasks.validate import load_task

FIXTURES = Path(__file__).parent / "fixtures" / "tasks"
VALID = FIXTURES / "valid" / "arabic-in-code-farewell"
REPO_TASKS = Path(__file__).parent.parent / "tasks"

DIALECT_PROMPT = """
[prompts.egy]
file = "prompts/egy.md"
lang = "ar"
kind = "dialect"
{dialect}review_status = "{status}"
"""


@pytest.fixture
def task(tmp_path):
    """A mutable copy of the valid sample."""
    root = tmp_path / "work"
    root.mkdir()
    dest = root / VALID.name
    shutil.copytree(VALID, dest)
    return dest


def add_dialect(task_dir: Path, dialect: str, status: str) -> None:
    """Append a dialect variant (with its own prompt file) to a task copy."""
    (task_dir / "prompts" / "egy.md").write_text("إزيك يا {name}\n", encoding="utf-8")
    line = f'dialect = "{dialect}"\n' if dialect else ""
    edit(task_dir, append=DIALECT_PROMPT.format(dialect=line, status=status))


def edit(task_dir: Path, old: str | None = None, new: str = "", append: str = "") -> None:
    """Replace text in (and/or append to) the task.toml of a task copy."""
    toml = task_dir / "task.toml"
    text = toml.read_text(encoding="utf-8")
    if old is not None:
        assert old in text, old
        text = text.replace(old, new)
    toml.write_text(text + append, encoding="utf-8")


def errors_of(task_dir: Path, strict: bool = False) -> str:
    return "\n".join(validate_task_dir(task_dir, strict=strict))


def make_native(task_dir: Path) -> None:
    """Mark every prompt already in the task copy as native_authored."""
    edit(task_dir, 'review_status = "draft"', 'review_status = "native_authored"')


def test_valid_fixture_passes():
    assert validate_task_dir(VALID) == []
    # the sample's en and msa prompts are AI drafts, so strict mode rejects both
    assert len(validate_task_dir(VALID, strict=True)) == 2


def test_strict_rejects_draft_english_and_msa(task):
    errors = validate_task_dir(task, strict=True)
    assert sum("review_status" in e and "strict" in e for e in errors) == 2


def test_strict_passes_when_every_prompt_is_native(task):
    make_native(task)
    assert validate_task_dir(task, strict=True) == []


def test_normal_mode_still_allows_drafts(task):
    assert validate_task_dir(task) == []


def test_real_tasks_dir_validates():
    count = len(list(REPO_TASKS.glob("*/*/task.toml")))  # counted without the validator
    assert count >= 6
    assert validate_paths([REPO_TASKS]) == (count, [])


def test_missing_required_field():
    errs = validate_task_dir(FIXTURES / "invalid" / "missing-title")
    assert any("task.toml" in e and "title" in e for e in errs)


def test_unknown_track(task):
    edit(task, 'track = "b-arabic-in-code"', 'track = "z-nope"')
    assert "track" in errors_of(task)


def test_id_must_equal_directory_name(task):
    edit(task, 'id = "arabic-in-code-farewell"', 'id = "something-else"')
    assert "id: 'something-else' must equal directory name" in errors_of(task)


@pytest.mark.parametrize("bad", ["1.0", "v1.0.0", "01.0.0", "latest"])
def test_bad_semver(task, bad):
    toml = task / "task.toml"
    text, n = re.subn(r'(?m)^version = "[^"]*"$', f'version = "{bad}"', toml.read_text("utf-8"))
    assert n == 1
    toml.write_text(text, encoding="utf-8")
    assert "version" in errors_of(task)


def test_no_english_prompt(task):
    edit(task, 'lang = "en"\nkind = "en"', 'lang = "ar"\nkind = "msa"')
    assert "lang = 'en'" in errors_of(task)


def test_no_arabic_prompt(task):
    edit(task, 'lang = "ar"\nkind = "msa"', 'lang = "en"\nkind = "en"')
    assert "lang = 'ar'" in errors_of(task)


def test_dialect_kind_requires_dialect(task):
    add_dialect(task, "", "draft")
    assert "dialect: required when kind is 'dialect'" in errors_of(task)


def test_dialect_draft_allowed_normally_rejected_in_strict(task):
    add_dialect(task, "egyptian", "draft")
    assert validate_task_dir(task) == []
    strict = errors_of(task, strict=True)
    assert "prompts.egy.review_status" in strict and "draft" in strict
    assert "Dialect and Arabizi prompts are never machine-written alone." in strict


def test_dialect_reviewed_passes_strict(task):
    make_native(task)
    add_dialect(task, "egyptian", "native_reviewed")
    assert validate_task_dir(task, strict=True) == []


def test_missing_prompt_file(task):
    (task / "prompts" / "msa.md").unlink()
    assert "prompts.msa.file: file not found" in errors_of(task)


def test_missing_grader_entry(task):
    (task / "tests" / "test.sh").unlink()
    assert "grader.entry" in errors_of(task)


def test_missing_solution_dirs(task):
    shutil.rmtree(task / "solutions" / "reference")
    shutil.rmtree(task / "solutions" / "known-bad")
    errs = errors_of(task)
    assert "solutions.reference" in errs and "solutions.known_bad" in errs


def test_identical_reference_and_known_bad(task):
    edit(task, 'known_bad = "solutions/known-bad"', 'known_bad = "solutions/reference"')
    assert "reference and known_bad must be different" in errors_of(task)


def test_prompt_with_bom(task):
    p = task / "prompts" / "msa.md"
    p.write_bytes(b"\xef\xbb\xbf" + p.read_bytes())
    assert "BOM" in errors_of(task)


def test_prompt_not_utf8(task):
    (task / "prompts" / "msa.md").write_bytes("مرحبا".encode("windows-1256"))
    assert "not valid UTF-8" in errors_of(task)


def test_heldout_in_public_tree_rejected():
    errs = validate_task_dir(FIXTURES / "invalid" / "heldout-in-public")
    assert any("split" in e and "heldout" in e for e in errs)


def make_heldout(task: Path, base: Path) -> Path:
    """Move a task copy to base/<name> and mark it heldout."""
    edit(task, 'split = "public"', 'split = "heldout"')
    base.mkdir(parents=True)
    return Path(shutil.move(str(task), base / task.name))


def test_heldout_allowed_under_tasks_heldout(task, tmp_path):
    moved = make_heldout(task, tmp_path / "tasks" / "heldout")
    assert validate_task_dir(moved) == []


def test_heldout_rejected_when_only_an_ancestor_is_named_heldout(task, tmp_path):
    moved = make_heldout(task, tmp_path / "heldout" / "repo" / "tasks" / "b-arabic-in-code")
    assert "split" in errors_of(moved)
    unnormalized = moved / ".." / ".." / ".." / ".." / "repo" / "tasks" / "b-arabic-in-code"
    assert "split" in errors_of(unnormalized / moved.name)


def test_heldout_without_tasks_ancestor_rejected(task, tmp_path):
    moved = make_heldout(task, tmp_path / "heldout")
    assert "split" in errors_of(moved)


def test_loader_does_not_alter_prompt_bytes():
    before = (VALID / "prompts" / "msa.md").read_bytes()
    spec = load_task(VALID)
    after = (VALID / spec.prompts["msa"].file).read_bytes()
    assert before == after
    # The fixture is the exact Arabic written in the brief and contains no BOM.
    text = after.decode("utf-8")
    assert "وداعاً يا {name}!" in text and "تحية.py" in text
    assert not after.startswith(b"\xef\xbb\xbf")


def test_cli_exit_codes(capsys):
    assert main(["validate-tasks", str(VALID)]) == 0
    capsys.readouterr()
    assert main(["validate-tasks", "--strict", str(VALID)]) == 1
    err = capsys.readouterr().err
    assert err.count("review_status") == 2 and "FAILED: 2 error(s)" in err
    assert main(["validate-tasks", str(FIXTURES / "invalid" / "missing-title")]) == 1
    err = capsys.readouterr().err
    assert "task.toml" in err and "title" in err
    assert main(["validate-tasks", str(FIXTURES / "nope")]) == 1


# --- QA fix round: containment, hardening, mutation-probe gaps ---


def symlink(link: Path, target: Path) -> None:
    if link.is_symlink() or link.is_file():
        link.unlink()
    elif link.is_dir():
        shutil.rmtree(link)
    link.symlink_to(target)


@pytest.fixture
def outside(tmp_path):
    out = tmp_path / "outside"
    (out / "dir").mkdir(parents=True)
    (out / "file.md").write_text("خارج\n", encoding="utf-8")
    return out


def test_symlinked_solution_dir_escaping_rejected(task, outside):
    symlink(task / "solutions" / "reference", outside / "dir")
    assert "solutions.reference" in errors_of(task)


def test_symlinked_prompt_escaping_rejected(task, outside):
    symlink(task / "prompts" / "msa.md", outside / "file.md")
    assert "prompts.msa.file" in errors_of(task)


def test_symlinked_grader_entry_escaping_rejected(task, outside):
    symlink(task / "tests" / "test.sh", outside / "file.md")
    assert "grader.entry" in errors_of(task)


def test_symlink_inside_task_dir_is_fine(task):
    (task / "solutions" / "alias").symlink_to(task / "solutions" / "reference")
    edit(task, 'known_bad = "solutions/known-bad"', 'known_bad = "solutions/known-bad"')
    assert validate_task_dir(task) == []


@pytest.mark.parametrize("bad", ["../outside", "/etc"])
def test_path_traversal_guard(task, bad):
    edit(task, 'file = "prompts/msa.md"', f'file = "{bad}"')
    edit(task, 'entry = "tests/test.sh"', f'entry = "{bad}"')
    edit(task, 'reference = "solutions/reference"', f'reference = "{bad}"')
    errs = errors_of(task)
    assert "prompts.msa.file: path must stay inside" in errs
    assert "grader.entry: not a file inside the task" in errs
    assert "solutions.reference: directory not found" in errs


def test_known_bad_path_traversal(task):
    edit(task, 'known_bad = "solutions/known-bad"', 'known_bad = "../x"')
    assert "solutions.known_bad: directory not found" in errors_of(task)


def test_non_utf8_task_toml(task):
    (task / "task.toml").write_bytes('schema_version = "1"'.encode("utf-16"))
    assert "task.toml" in errors_of(task)


def test_invalid_toml(task):
    edit(task, append="\n[[[broken")
    assert "invalid TOML" in errors_of(task)


@pytest.mark.parametrize("content", [b"", b"  \n\t\n", b"abc\x00def"])
def test_prompt_empty_blank_or_nul(task, content):
    (task / "prompts" / "msa.md").write_bytes(content)
    assert "prompts.msa.file" in errors_of(task)


def test_kind_en_requires_lang_en(task):
    edit(task, 'lang = "ar"\nkind = "msa"', 'lang = "ar"\nkind = "en"')
    assert "lang" in errors_of(task)


def test_kind_msa_requires_lang_ar(task):
    edit(task, 'lang = "ar"\nkind = "msa"', 'lang = "en"\nkind = "msa"')
    assert "lang" in errors_of(task)


@pytest.mark.parametrize(
    "old,new",
    [
        ('entry = "tests/test.sh"', 'entry = "  "'),
        ('entry = "tests/test.sh"', 'entry = ""'),
    ],
)
def test_grader_blank_entry(task, old, new):
    edit(task, old, new)
    assert "grader" in errors_of(task)


@pytest.mark.parametrize("entry", ["tests", "."])
def test_grader_entry_must_be_a_file(task, entry):
    edit(task, 'entry = "tests/test.sh"', f'entry = "{entry}"')
    assert "grader.entry" in errors_of(task)


@pytest.mark.parametrize(
    "ref,bad",
    [
        ("solutions", "solutions/known-bad"),
        ("solutions/reference", "solutions/reference/sub"),
        (".", "solutions/known-bad"),
    ],
)
def test_solutions_must_not_nest_or_be_task_root(task, ref, bad):
    (task / "solutions" / "reference" / "sub").mkdir()
    edit(task, 'reference = "solutions/reference"', f'reference = "{ref}"')
    edit(task, 'known_bad = "solutions/known-bad"', f'known_bad = "{bad}"')
    assert "solutions" in errors_of(task)


def test_identical_solutions_via_different_spelling(task):
    edit(task, 'known_bad = "solutions/known-bad"', 'known_bad = "solutions/./reference"')
    assert "must be different" in errors_of(task)


def test_empty_pair_id(task):
    edit(task, 'pair_id = "arabic-in-code-farewell"', 'pair_id = ""')
    assert "pair_id" in errors_of(task)


@pytest.mark.parametrize("title", ["", "   "])
def test_blank_title(task, title):
    edit(task, 'title = "Add a function without altering Arabic bytes"', f'title = "{title}"')
    assert "title" in errors_of(task)


def test_two_variants_same_file(task):
    edit(task, 'file = "prompts/en.md"', 'file = "prompts/msa.md"')
    assert "same file" in errors_of(task)


def test_missing_fixture_dir(task):
    shutil.rmtree(task / "fixture")
    assert "missing required directory fixture/" in errors_of(task)


def test_missing_tests_dir(task):
    shutil.rmtree(task / "tests")
    assert "missing required directory tests/" in errors_of(task)


def test_missing_dockerfile(task):
    (task / "environment" / "Dockerfile").unlink()
    assert "environment/Dockerfile" in errors_of(task)


def test_dialect_on_non_dialect_kind(task):
    edit(task, 'kind = "msa"', 'kind = "msa"\ndialect = "gulf"')
    assert "dialect: only allowed when kind is 'dialect'" in errors_of(task)


def test_id_must_be_kebab_case(task, tmp_path):
    bad = task.rename(task.parent / "Bad_ID")
    edit(bad, 'id = "arabic-in-code-farewell"', 'id = "Bad_ID"')
    errs = errors_of(bad)
    assert "id" in errs and "must equal directory name" not in errs


def test_unknown_field_rejected(task):
    edit(task, 'stack = ["python"]', 'stack = ["python"]\nsurprise = 1')
    assert "surprise" in errors_of(task)


@pytest.mark.parametrize("value", ["0", "-5"])
def test_timeout_must_be_positive(task, value):
    edit(task, "timeout_seconds = 120", f"timeout_seconds = {value}")
    assert "grader.timeout_seconds" in errors_of(task)


def test_missing_solve_sh_in_reference(task):
    (task / "solutions/reference/solve.sh").unlink()
    assert "solutions.reference: missing solve.sh" in errors_of(task)


def test_missing_solve_sh_in_known_bad(task):
    (task / "solutions/known-bad/solve.sh").unlink()
    assert "solutions.known_bad: missing solve.sh" in errors_of(task)


def test_grader_entry_must_be_inside_tests(task):
    (task / "run.sh").write_text("#!/bin/bash\n")
    edit(task, 'entry = "tests/test.sh"', 'entry = "run.sh"')
    assert "grader.entry: must be inside tests/" in errors_of(task)


def test_grader_command_field_is_rejected(task):
    edit(task, 'entry = "tests/test.sh"', 'entry = "tests/test.sh"\ncommand = "x"')
    assert "grader.command" in errors_of(task)


def test_grader_entry_is_required(task):
    edit(task, 'entry = "tests/test.sh"\n', "")
    assert "grader.entry" in errors_of(task)


# --- Second QA round: symlink loops and required paths containment ---


def test_symlink_loop_in_prompt_file(task):
    msa = task / "prompts" / "msa.md"
    msa.unlink()
    msa.symlink_to(msa)
    assert "prompts.msa.file" in errors_of(task)


def test_symlink_loop_as_tests_dir(task):
    shutil.rmtree(task / "tests")
    (task / "tests").symlink_to(task / "tests")
    errs = errors_of(task)
    assert "tests/" in errs and "grader.entry" in errs


def test_symlinked_fixture_dir_escaping_rejected(task, outside):
    symlink(task / "fixture", outside / "dir")
    assert "missing required directory fixture/" in errors_of(task)


def test_symlinked_tests_dir_escaping_rejected(task, outside):
    symlink(task / "tests", outside / "dir")
    assert "missing required directory tests/" in errors_of(task)


def test_symlinked_dockerfile_escaping_rejected(task, outside):
    symlink(task / "environment" / "Dockerfile", outside / "file.md")
    assert "environment/Dockerfile" in errors_of(task)


def test_symlinked_fixture_and_dockerfile_inside_task_allowed(task):
    real = task / "fixture_real"
    (task / "fixture").rename(real)
    (task / "fixture").symlink_to(real)
    docker = task / "environment" / "Dockerfile"
    (task / "Dockerfile.real").write_bytes(docker.read_bytes())
    docker.unlink()
    docker.symlink_to(task / "Dockerfile.real")
    assert validate_task_dir(task) == []


# --- Third round: script field (Arabizi variants) ---


def add_variant(task_dir: Path, name: str, extra: str, status: str = "draft", **kw: str) -> None:
    """Append a [prompts.<name>] variant with its own placeholder prompt file."""
    (task_dir / "prompts" / f"{name}.md").write_text("ana 3ayez a7sen\n", encoding="utf-8")
    fields = {"lang": "ar", "kind": "dialect", **kw}
    body = "".join(f'{k} = "{v}"\n' for k, v in fields.items())
    edit(
        task_dir,
        append=f'\n[prompts.{name}]\nfile = "prompts/{name}.md"\n{body}{extra}'
        f'review_status = "{status}"\n',
    )


def add_arabizi(task_dir: Path, name: str = "arabizi_egy_a", status: str = "draft") -> None:
    add_variant(task_dir, name, 'dialect = "egyptian"\nscript = "latin"\n', status)


def test_invalid_script_value(task):
    add_variant(task, "x", 'dialect = "egyptian"\nscript = "cyrillic"\n')
    assert "prompts.x.script" in errors_of(task)


def test_script_latin_requires_lang_ar(task):
    add_variant(task, "x", 'script = "latin"\n', lang="en", kind="en")
    assert "script: 'latin' requires lang 'ar'" in errors_of(task)


def test_arabizi_alone_does_not_satisfy_arabic_requirement(task):
    edit(task, 'lang = "ar"\nkind = "msa"', 'lang = "ar"\nkind = "msa"\nscript = "latin"')
    assert "script = 'arabic'" in errors_of(task)


def test_mixed_task_with_arabizi_passes_normal_not_strict_until_reviewed(task):
    add_arabizi(task, "arabizi_egy_a")
    add_arabizi(task, "arabizi_egy_b")
    assert validate_task_dir(task) == []
    strict = errors_of(task, strict=True)
    assert "prompts.arabizi_egy_a.review_status" in strict
    assert "Dialect and Arabizi prompts are never machine-written alone." in strict
    assert "prompts.arabizi_egy_b.review_status" in strict


def test_arabizi_reviewed_passes_strict(task):
    make_native(task)
    add_arabizi(task, "arabizi_egy_a", status="native_reviewed")
    assert validate_task_dir(task, strict=True) == []


def test_draft_latin_code_switched_rejected_in_strict(task):
    add_variant(task, "cs", 'script = "latin"\n', kind="code-switched")
    assert validate_task_dir(task) == []
    assert "prompts.cs.review_status" in errors_of(task, strict=True)


# --- QA fix round: solve.sh, entry containment, Dockerfile sources ---


def test_solve_sh_directory_is_rejected(task):
    solve = task / "solutions/reference/solve.sh"
    solve.unlink()
    solve.mkdir()
    assert "solutions.reference: missing solve.sh" in errors_of(task)


@pytest.mark.parametrize("folder", ["testing", "tests2"])
def test_grader_entry_near_miss_prefix_rejected(task, folder):
    (task / folder).mkdir()
    (task / folder / "x.sh").write_text("#!/bin/bash\n")
    edit(task, 'entry = "tests/test.sh"', f'entry = "{folder}/x.sh"')
    assert "grader.entry: must be inside tests/" in errors_of(task)


def test_grader_entry_symlink_leaving_tests_is_rejected(task):
    (task / "other.sh").write_text("#!/bin/bash\n")
    (task / "tests" / "run.sh").symlink_to("../other.sh")
    edit(task, 'entry = "tests/test.sh"', 'entry = "tests/run.sh"')
    assert "grader.entry: must be inside tests/" in errors_of(task)


def set_dockerfile(task_dir: Path, text: str) -> None:
    (task_dir / "environment" / "Dockerfile").write_text(text, encoding="utf-8")


@pytest.mark.parametrize(
    "line",
    [
        "COPY tests/ /x",
        "COPY solutions/ /x",
        "ADD . /app",
        "copy tests/ /x",
        "COPY --chown=1:1 tests/ /x",
        "COPY fixture/ tests/ /app/",
        "COPY fixture/../tests /x",
        "COPY /etc/passwd /x",
        'COPY ["tests/", "/x"]',
        "COPY fixture/ \\\n  tests/ /app/",
        "ADD https://example.com/x.tar /x",
    ],
)
def test_dockerfile_rejects_sources_outside_fixture(task, line):
    set_dockerfile(task, f"FROM python:3.12-slim\n{line.replace(chr(92) + 'n', chr(10))}\n")
    errs = errors_of(task)
    assert "environment/Dockerfile" in errs and "fixture/" in errs


@pytest.mark.parametrize(
    "line",
    [
        "COPY fixture/ /app/",
        "COPY fixture /app/",
        "COPY --chown=1:1 fixture/ /app/",
        "COPY --chmod=755 --chown=1:1 fixture/ /app/",
        "COPY --from=build /a /b",
        'COPY ["fixture/", "/app/"]',
        "add fixture/x.txt /app/",
        "COPY fixture/a fixture/b /app/",
        "COPY fixture/ \\\n  /app/",
        "# COPY tests/ /x",
    ],
)
def test_dockerfile_accepts_fixture_sources(task, line):
    set_dockerfile(task, f"FROM python:3.12-slim\n{line.replace(chr(92) + 'n', chr(10))}\n")
    assert validate_task_dir(task) == []


def test_dockerfile_error_names_the_line(task):
    set_dockerfile(task, "FROM python:3.12-slim\nWORKDIR /app\nCOPY tests/ /x\n")
    assert "Dockerfile: line 3" in errors_of(task)


@pytest.mark.parametrize(
    "mount",
    [
        "type=bind,source=tests,target=/x",
        "type=bind,source=solutions,target=/x",
        "type=bind,source=.,target=/x",
        "source=tests,target=/x",
        "target=/x",
        "type=bind,target=/x",
        "TYPE=BIND,source=tests,target=/x",
    ],
)
def test_dockerfile_rejects_bind_mounts_from_the_context(task, mount):
    set_dockerfile(task, f"FROM python:3.12-slim\nRUN --mount={mount} ls /x\n")
    errs = errors_of(task)
    assert "environment/Dockerfile: line 2" in errs and "--mount" in errs


@pytest.mark.parametrize(
    "mount",
    [
        "type=cache,target=/root/.cache",
        "type=tmpfs,target=/tmp/x",
        "type=secret,id=x",
        "type=ssh",
        "type=bind,from=build,source=/x,target=/y",
    ],
)
def test_dockerfile_accepts_other_mounts_and_bind_from_stage(task, mount):
    set_dockerfile(task, f"FROM python:3.12-slim\nRUN --mount={mount} ls /x\n")
    assert validate_task_dir(task) == []


def test_dockerfile_rejects_bind_mount_among_several_flags(task):
    set_dockerfile(
        task,
        "FROM python:3.12-slim\n"
        "RUN --network=none --mount=type=cache,target=/c --mount=type=bind,source=tests,"
        "target=/x ls\n",
    )
    assert "--mount" in errors_of(task)


@pytest.mark.parametrize("line", ['COPY "fixture/" /app/', "COPY 'fixture/' /app/"])
def test_dockerfile_accepts_quoted_fixture_source(task, line):
    set_dockerfile(task, f"FROM python:3.12-slim\n{line}\n")
    assert validate_task_dir(task) == []


def test_dockerfile_rejects_quoted_source_outside_fixture(task):
    set_dockerfile(task, 'FROM python:3.12-slim\nCOPY "tests/" /x\n')
    assert "fixture/" in errors_of(task)


@pytest.mark.parametrize("key", ["x/../../victim", "a/b", "..", "Up", "-x", "a b", "_x", ""])
def test_variant_key_must_be_a_safe_name(task, key):
    shutil.copy(task / "prompts/en.md", task / "prompts/other.md")
    edit(
        task,
        append=f'\n[prompts."{key}"]\nfile = "prompts/other.md"\nlang = "en"\nkind = "en"\n'
        'review_status = "native_authored"\n',
    )
    errors = validate_task_dir(task)
    assert any("variant name" in e for e in errors), errors


def test_real_variant_keys_pass():
    assert validate_paths([REPO_TASKS])[1] == []


@pytest.mark.parametrize(("length", "ok"), [(64, True), (65, False)])
def test_variant_key_length_cap(task, length, ok):
    shutil.copy(task / "prompts/en.md", task / "prompts/other.md")
    key = "a" * length
    edit(
        task,
        append=f'\n[prompts.{key}]\nfile = "prompts/other.md"\nlang = "en"\nkind = "en"\n'
        'review_status = "native_authored"\n',
    )
    errors = validate_task_dir(task)
    assert (not any("variant name" in e for e in errors)) is ok, errors


def test_valid_fixture_matches_the_real_task():
    """Docker selftests run this fixture, so its grading files must not drift from the real task.

    Prompts and task.toml may differ: the sample keeps an MSA variant the validator tests use."""
    real = Path(__file__).parent.parent / "tasks" / "b-arabic-in-code" / "arabic-in-code-farewell"

    def files(root):
        return {
            p.relative_to(root): p.read_bytes()
            for p in root.rglob("*")
            if p.is_file()
            and p.name not in ("REVIEW.md", "task.toml")
            and "__pycache__" not in p.parts
            and p.relative_to(root).parts[0] != "prompts"
        }

    assert files(VALID) == files(real)
