import hashlib
import json
import os
import re
import shutil
import tomllib
from pathlib import Path

import pytest

from kilmeh.cli import main
from kilmeh.harbor import export_paths, export_task

REPO_TASKS = Path(__file__).parent.parent / "tasks"
LOOP = REPO_TASKS / "a-prompts" / "loop-for-to-while"
FAREWELL = REPO_TASKS / "b-arabic-in-code" / "arabic-in-code-farewell"
# Same pins as tests/test_seed_tasks.py (board-authored prompts).
BOARD_PROMPT_SHA256 = {
    "en.md": "cadc05e394945ba18746987c02925d54bb3b20b7a48424b567341dc0a63cf87f",
    "arabizi_levantine.md": "56b86e680d27ce0e85b93ae4ee5b0cf826d91e2edfb50f9b56cd8e489cff34ab",
    "levantine.md": "60c716ec63dc2944a8a7a1b5a04ee17c96db597de8b335c7d13c9bc10dafaf18",
}
VALID = Path(__file__).parent / "fixtures" / "tasks" / "valid" / "arabic-in-code-farewell"


@pytest.fixture
def out(tmp_path):
    dest = tmp_path / "out"
    export_paths([REPO_TASKS], dest)
    return dest


@pytest.fixture
def tmp_task(tmp_path):
    dest = tmp_path / "work" / "tasks" / VALID.name
    shutil.copytree(VALID, dest)
    return dest


def mark_native(task: Path) -> Path:
    """Mark every prompt native_authored so the AI-draft skip does not hide a variant."""
    toml = task / "task.toml"
    text = toml.read_text("utf-8")
    toml.write_text(
        text.replace('review_status = "draft"', 'review_status = "native_authored"'), "utf-8"
    )
    return task


def digests(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


PLACEHOLDER = b"TODO(board)"


def real_variant_count() -> int:
    """Variants that are neither board placeholders nor non-English AI drafts (counted from
    task.toml without the exporter)."""
    count = 0
    for toml in REPO_TASKS.glob("*/*/task.toml"):
        for p in tomllib.loads(toml.read_text("utf-8"))["prompts"].values():
            if p["lang"] != "en" and p["review_status"] == "draft":
                continue
            if not (toml.parent / p["file"]).read_bytes().startswith(PLACEHOLDER):
                count += 1
    return count


def test_placeholder_variants_are_not_exported(out):
    names = sorted(p.name for p in out.iterdir())
    assert len(names) == real_variant_count()
    assert "rtl-nav-fix--en" in names
    assert "rtl-nav-fix--levantine" in names  # board-approved Jordanian variant is exported
    for folder in out.iterdir():
        assert not (folder / "instruction.md").read_bytes().startswith(PLACEHOLDER)


def test_placeholder_skip_both_ways(tmp_task, tmp_path):
    mark_native(tmp_task)
    prompts = tmp_task / "prompts"
    msa = prompts / "msa.md"
    original = msa.read_bytes()
    assert [f.name for f in export_task(tmp_task, tmp_path / "real")] == [
        "arabic-in-code-farewell--en",
        "arabic-in-code-farewell--msa",
    ]
    msa.write_bytes(b"TODO(board): native prompt, see REVIEW.md\n")
    folders = export_task(tmp_task, tmp_path / "placeholder")
    assert [f.name for f in folders] == ["arabic-in-code-farewell--en"]
    assert not (tmp_path / "placeholder" / "arabic-in-code-farewell--msa").exists()
    # only a prompt that STARTS with the marker is skipped
    msa.write_bytes(b"Mentions TODO(board) later in the text\n")
    assert len(export_task(tmp_task, tmp_path / "mid")) == 2
    msa.write_bytes(original)
    assert len(export_task(tmp_task, tmp_path / "restored")) == 2


def test_ai_draft_arabic_variants_are_not_exported(out):
    names = sorted(p.name for p in out.iterdir())
    assert "arabic-in-code-farewell--msa" not in names  # AI-written MSA, review_status draft
    assert "arabic-in-code-farewell--en" in names  # an English draft is still exported
    for folder in out.iterdir():
        meta = tomllib.loads((folder / "task.toml").read_text("utf-8"))["metadata"]
        assert meta["lang"] == "en" or meta["review_status"] != "draft", folder.name


@pytest.mark.parametrize(
    ("status", "exported"),
    [("draft", False), ("native_authored", True), ("native_reviewed", True)],
)
def test_arabic_variant_export_follows_review_status(tmp_task, tmp_path, status, exported):
    toml = tmp_task / "task.toml"
    text = toml.read_text("utf-8")
    msa = text.index("[prompts.msa]")
    toml.write_text(
        text[:msa]
        + text[msa:].replace('review_status = "draft"', f'review_status = "{status}"', 1),
        "utf-8",
    )
    names = [f.name for f in export_task(tmp_task, tmp_path / "o")]
    assert ("arabic-in-code-farewell--msa" in names) is exported
    assert "arabic-in-code-farewell--en" in names  # the English prompt stays a draft


def test_draft_arabizi_variant_is_not_exported(tmp_task, tmp_path):
    mark_native(tmp_task)  # the MSA variant is native, so only the draft Arabizi is skipped
    shutil.copy(tmp_task / "prompts/msa.md", tmp_task / "prompts/arabizi.md")
    extra = (
        '\n[prompts.arabizi]\nfile = "prompts/arabizi.md"\nlang = "ar"\nkind = "dialect"\n'
        'dialect = "egyptian"\nscript = "latin"\nreview_status = "draft"\n'
    )
    toml = tmp_task / "task.toml"
    toml.write_text(toml.read_text("utf-8") + extra, "utf-8")
    names = [f.name for f in export_task(tmp_task, tmp_path / "o")]
    assert names == ["arabic-in-code-farewell--en", "arabic-in-code-farewell--msa"]


def test_rtl_export_is_self_contained(out):
    rtl = sorted(p for p in out.iterdir() if p.name.startswith("rtl-"))
    assert rtl, "no exported RTL folders"
    for folder in rtl:
        tests = folder / "tests"
        for name in ("rtl_checks.py", "build.sh", "verify.py", "test.sh"):
            assert (tests / name).is_file(), f"{folder.name}/tests/{name}"
        for script in (tests / "verify.py", tests / "build.sh"):
            text = script.read_text(encoding="utf-8")
            for ref in ("../", "solutions/", "fixture/"):
                assert f'"{ref}' not in text and f"'{ref}" not in text, f"{script}: {ref}"
        # every file verify.py reads next to itself is in the exported tests/ folder
        for name in re.findall(r'HERE / "([^"]+)"', (tests / "verify.py").read_text("utf-8")):
            assert (tests / name).is_file(), f"{folder.name}: tests/{name} missing"


def test_one_folder_per_variant(out):
    names = sorted(p.name for p in out.iterdir())
    assert [n for n in names if n.startswith("loop-for-to-while--")] == [
        "loop-for-to-while--arabizi_levantine",
        "loop-for-to-while--en",
        "loop-for-to-while--levantine",
    ]
    assert [n for n in names if n.startswith("arabic-in-code-farewell--")] == [
        "arabic-in-code-farewell--en"
    ]


def test_instruction_bytes_equal_prompt(out):
    prompts = [*sorted((LOOP / "prompts").iterdir()), FAREWELL / "prompts/en.md"]
    for prompt in prompts:
        folder = out / f"{prompt.parent.parent.name}--{prompt.stem}"
        assert (folder / "instruction.md").read_bytes() == prompt.read_bytes()
    for name, expected in BOARD_PROMPT_SHA256.items():
        data = (out / f"loop-for-to-while--{Path(name).stem}" / "instruction.md").read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected


def test_fixture_copied_byte_identical(out):
    for folder in out.glob("arabic-in-code-farewell--*"):
        fixture = folder / "environment" / "fixture"
        for src in (FAREWELL / "fixture").iterdir():
            assert (fixture / src.name).read_bytes() == src.read_bytes()
        assert "تحية.py" in [p.name for p in fixture.iterdir()]


def test_layout(out):
    for folder in out.iterdir():
        for rel in (
            "instruction.md",
            "task.toml",
            "environment/Dockerfile",
            "tests/test.sh",
            "solution/solve.sh",
        ):
            assert (folder / rel).is_file(), f"{folder.name}/{rel}"
        assert (folder / "environment/fixture").is_dir()


def test_known_bad_never_exported(out):
    assert not [p for p in out.rglob("*") if "known-bad" in p.as_posix()]
    got = out / "arabic-in-code-farewell--en/solution/solve.py"
    ref = FAREWELL / "solutions/reference/solve.py"
    bad = FAREWELL / "solutions/known-bad/solve.py"
    assert got.read_bytes() == ref.read_bytes()
    assert got.read_bytes() != bad.read_bytes()


def test_task_toml_round_trip(out):
    d = tomllib.loads((out / "loop-for-to-while--arabizi_levantine/task.toml").read_text("utf-8"))
    assert d["schema_version"] == "1.4"
    assert d["task"]["name"] == "kilmeh/loop-for-to-while--arabizi_levantine"
    assert d["metadata"] == {
        "kilmeh_task_id": "loop-for-to-while",
        "kilmeh_task_version": "0.1.0",
        "track": "a-prompts",
        "difficulty": "easy",
        "split": "public",
        "pair_id": "loop-for-to-while",
        "variant": "arabizi_levantine",
        "lang": "ar",
        "kind": "dialect",
        "script": "latin",
        "dialect": "levantine",
        "review_status": "native_authored",
    }
    assert d["verifier"]["timeout_sec"] == 120
    assert d["agent"]["timeout_sec"] == 900
    assert d["environment"]["build_timeout_sec"] == 600


def test_optional_metadata_omitted(out):
    d = tomllib.loads((out / "loop-for-to-while--en/task.toml").read_text("utf-8"))
    assert "dialect" not in d["metadata"]


def test_title_with_quotes_and_arabic_survives_toml(tmp_task, tmp_path):
    toml = tmp_task / "task.toml"
    text = toml.read_text("utf-8")
    title = 'a "b" \\ ع'
    new = "title = '" + title + "'"
    toml.write_text(re.sub(r"(?m)^title = .*$", lambda _: new, text), "utf-8")
    out = tmp_path / "o"
    export_task(tmp_task, out)
    d = tomllib.loads((out / f"{tmp_task.name}--en/task.toml").read_text("utf-8"))
    assert d["task"]["description"] == title


def test_stale_files_are_removed(out):
    stale = out / "loop-for-to-while--en" / "stale.txt"
    stale.write_text("old")
    nested = out / "loop-for-to-while--en/environment/fixture/stale2"
    nested.write_text("old")
    export_paths([REPO_TASKS], out)
    assert not stale.exists()
    assert not nested.exists()


def test_export_is_deterministic(tmp_path):
    export_paths([REPO_TASKS], tmp_path / "a")
    export_paths([REPO_TASKS], tmp_path / "b")
    assert digests(tmp_path / "a") == digests(tmp_path / "b")


def test_heldout_task_is_refused(tmp_task, tmp_path):
    heldout = tmp_task.parent / "heldout" / tmp_task.name
    heldout.parent.mkdir()
    shutil.move(tmp_task, heldout)
    toml = heldout / "task.toml"
    toml.write_text(
        toml.read_text("utf-8").replace('split = "public"', 'split = "heldout"'), "utf-8"
    )
    out = tmp_path / "o"
    with pytest.raises(ValueError, match="held-out"):
        export_task(heldout, out)
    with pytest.raises(ValueError, match="held-out"):
        export_paths([heldout], out)
    assert not out.exists()
    assert main(["export-harbor", str(out), str(heldout)]) == 1
    assert not out.exists()


def test_cli_exit_1_on_invalid_task(tmp_task, tmp_path, capsys):
    (tmp_task / "prompts/en.md").unlink()
    out = tmp_path / "o"
    assert main(["export-harbor", str(out), str(tmp_task)]) == 1
    assert not out.exists()
    assert "error:" in capsys.readouterr().err


def test_cli_prints_one_folder_per_line(tmp_path, capsys):
    out = tmp_path / "o"
    assert main(["export-harbor", str(out), str(REPO_TASKS)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == real_variant_count()
    assert all(Path(line).is_dir() for line in lines)


def test_paths_with_spaces(tmp_task, tmp_path):
    spaced = tmp_path / "with space" / tmp_task.name
    shutil.copytree(tmp_task, spaced)
    folders = export_task(mark_native(spaced), tmp_path / "out dir")
    assert len(folders) == 2
    exported = folders[0] / "environment/fixture/تحية.py"
    assert exported.read_bytes() == (tmp_task / "fixture/تحية.py").read_bytes()


def test_scripts_are_executable(out):
    for folder in out.iterdir():
        for rel in ("solution/solve.sh", "tests/test.sh"):
            assert os.stat(folder / rel).st_mode & 0o100, f"{folder.name}/{rel}"


def test_variant_key_cannot_escape_out_dir(tmp_task, tmp_path):
    toml = tmp_task / "task.toml"
    shutil.copy(tmp_task / "prompts/msa.md", tmp_task / "prompts/evil.md")
    extra = '\n[prompts."x/../../victim"]\nfile = "prompts/msa.md"\nlang = "ar"\nkind = "msa"\n'
    extra = extra.replace("msa.md", "evil.md")
    toml.write_text(
        toml.read_text("utf-8") + extra + 'review_status = "native_authored"\n', "utf-8"
    )
    victim = tmp_path / "victim"
    victim.mkdir()
    (victim / "keep.txt").write_text("keep")
    out = tmp_path / "out"
    for _ in range(2):
        assert main(["export-harbor", str(out), str(tmp_task)]) == 1
    assert (victim / "keep.txt").exists()


def test_dest_outside_out_dir_is_refused(tmp_task, tmp_path, monkeypatch):
    # defense in depth: even if validation were bypassed, harbor refuses the dest itself
    import kilmeh.harbor as h

    spec = h.load_task(tmp_task)
    spec.prompts["x/../../victim"] = spec.prompts.pop("en")
    victim = tmp_path / "victim"
    victim.mkdir()
    (victim / "keep.txt").write_text("keep")
    with pytest.raises(ValueError, match="outside"):
        h._export(tmp_task, spec, tmp_path / "out")
    assert (victim / "keep.txt").exists()


def test_pycache_and_ds_store_not_copied(tmp_task, tmp_path):
    (tmp_task / "tests/__pycache__").mkdir()
    (tmp_task / "tests/__pycache__/x.cpython-312.pyc").write_bytes(b"x")
    (tmp_task / "tests/stray.pyc").write_bytes(b"x")
    (tmp_task / "fixture/.DS_Store").write_bytes(b"x")
    (tmp_task / "solutions/reference/__pycache__").mkdir()
    (tmp_task / "solutions/reference/__pycache__/y.pyc").write_bytes(b"x")
    out = tmp_path / "o"
    export_task(tmp_task, out)
    bad = [
        p for p in out.rglob("*") if p.name in ("__pycache__", ".DS_Store") or p.suffix == ".pyc"
    ]
    assert not bad


@pytest.mark.parametrize("kind", ["file", "symlink"])
def test_existing_variant_path_file_or_symlink_is_a_clear_error(tmp_task, tmp_path, kind, capsys):
    out = tmp_path / "o"
    out.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    (target / "keep.txt").write_text("keep")
    dest = out / f"{tmp_task.name}--en"
    if kind == "file":
        dest.write_text("x")
    else:
        dest.symlink_to(target, target_is_directory=True)
    assert main(["export-harbor", str(out), str(tmp_task)]) == 1
    assert "error:" in capsys.readouterr().err
    assert (target / "keep.txt").exists()
    assert dest.is_symlink() or dest.is_file()


def test_control_chars_in_title_survive_toml(tmp_task, tmp_path):
    title = "a\x7fb\x01c\x1bd ع"
    toml = tmp_task / "task.toml"
    new = f"title = {json.dumps(title)}"
    toml.write_text(re.sub(r"(?m)^title = .*$", lambda _: new, toml.read_text("utf-8")), "utf-8")
    out = tmp_path / "o"
    export_task(tmp_task, out)
    d = tomllib.loads((out / f"{tmp_task.name}--en/task.toml").read_text("utf-8"))
    assert d["task"]["description"] == title


def test_non_standard_grader_entry_is_refused(tmp_task, tmp_path):
    (tmp_task / "tests/other.sh").write_text("#!/bin/bash\n")
    toml = tmp_task / "task.toml"
    toml.write_text(toml.read_text("utf-8").replace("tests/test.sh", "tests/other.sh"), "utf-8")
    out = tmp_path / "o"
    with pytest.raises(ValueError, match="test.sh"):
        export_paths([tmp_task], out)
    assert not out.exists()


def test_export_task_returns_folders_sorted_by_variant(tmp_task, tmp_path):
    folders = export_task(mark_native(tmp_task), tmp_path / "o")
    assert [f.name for f in folders] == sorted(f.name for f in folders)
    assert len(folders) == 2


def test_oserror_while_writing_is_a_one_line_error(tmp_task, tmp_path, capsys, monkeypatch):
    import kilmeh.harbor as h

    def boom(*a, **k):
        raise OSError(63, "File name too long")

    monkeypatch.setattr(h.shutil, "copytree", boom)
    assert main(["export-harbor", str(tmp_path / "o"), str(tmp_task)]) == 1
    err = capsys.readouterr().err
    assert err.startswith("error:") and "Traceback" not in err


@pytest.mark.parametrize("kind", ["file", "symlink"])
def test_refusal_writes_nothing_earlier(tmp_task, tmp_path, kind):
    out = tmp_path / "o"
    out.mkdir()
    second = out / f"{tmp_task.name}--msa"  # variants sort en, msa
    if kind == "file":
        second.write_text("x")
    else:
        second.symlink_to(tmp_path, target_is_directory=True)
    before = sorted(p.name for p in out.iterdir())
    with pytest.raises(ValueError, match="symlink" if kind == "symlink" else "not a plain"):
        export_paths([tmp_task], out)
    assert sorted(p.name for p in out.iterdir()) == before
