import shutil
from pathlib import Path

import pytest

from kilmeh.arabizi_key import has_arabic_letter, split_of
from kilmeh.cli import main

FIXTURES = Path(__file__).parent / "fixtures" / "arabizi"
REPO_DATA = Path(__file__).parent.parent / "data" / "arabizi"


def run(path: Path, capsys) -> tuple[int, str]:
    code = main(["validate-arabizi", str(path)])
    return code, capsys.readouterr().err


def test_repo_data_is_valid(capsys):
    assert run(REPO_DATA, capsys) == (0, "")


def test_repo_template_has_fifty_empty_ids():
    lines = (REPO_DATA / "template" / "board-starter.jsonl").read_text("utf-8").splitlines()
    assert len(lines) == 50
    assert '"id": "jo-0001"' in lines[0] and '"id": "jo-0050"' in lines[-1]


def test_mapping_is_marked_draft_and_parses():
    import tomllib

    text = (REPO_DATA / "mapping.toml").read_text("utf-8")
    assert text.startswith("# AI draft: board review pending")
    table = tomllib.loads(text)
    assert table["digits"]["3"] == ["ع"] and "ش" in table["digraphs"]["sh"]


def test_valid_fixture_passes(capsys):
    assert run(FIXTURES / "valid", capsys) == (0, "")


def test_default_path_is_data_arabizi(capsys, monkeypatch):
    monkeypatch.chdir(REPO_DATA.parent.parent)
    assert main(["validate-arabizi"]) == 0


def test_missing_directory_fails(tmp_path, capsys):
    code, err = run(tmp_path / "nope", capsys)
    assert code == 1 and "not a directory" in err


BROKEN = [
    ("missing-field", "train.jsonl:1: field 'country': missing"),
    ("duplicate-id", "train.jsonl:2: field 'id': duplicate id 't-0001'"),
    ("invalid-utf8", "not valid UTF-8"),
    ("bom", "train.jsonl:1: file starts with a BOM"),
    ("crlf", "line endings must be LF only"),
    ("empty-text", "train.jsonl:1: field 'arabizi': must not be empty"),
    ("no-arabic-letter", "train.jsonl:1: field 'arabic': contains no Arabic letter"),
    ("arabic-in-arabizi", "train.jsonl:1: field 'arabizi': contains Arabic-script"),
    ("bad-source", "train.jsonl:1: field 'source': must be one of"),
    ("bad-authors", "train.jsonl:1: field 'authors': must be 1 or 2"),
    ("bad-dialect", "train.jsonl:1: field 'dialect': must be one of"),
    ("wrong-split-test-in-train", "'t-0014' belongs in test.jsonl, found in train.jsonl"),
    ("wrong-split-train-in-test", "'t-0001' belongs in train.jsonl, found in test.jsonl"),
    ("unknown-field", "train.jsonl:1: field 'extra': unknown field"),
    ("id-whitespace", "field 'id': must not have leading or trailing whitespace"),
    ("control-char", "train.jsonl:1: field 'arabizi': contains a control character"),
    ("authors-float", "train.jsonl:1: field 'authors': must be 1 or 2"),
    ("authors-bool", "train.jsonl:1: field 'authors': must be 1 or 2"),
    ("duplicate-key", "invalid JSON (duplicate key 'authors')"),
    ("lone-surrogate", "train.jsonl:1: field 'arabizi': contains a lone surrogate"),
    ("template-bad-script", "t.jsonl:1: field 'arabizi': contains Arabic-script"),
    ("empty-country", "train.jsonl:1: field 'country': must be a non-empty string"),
    ("notes-not-string", "train.jsonl:1: field 'notes': must be a string"),
    ("bad-alt-arabic", "train.jsonl:1: field 'alt_arabic': must be a list of Arabic strings"),
    ("blank-line", "train.jsonl:2: blank line"),
    ("non-object-line", "train.jsonl:1: line must be a JSON object"),
    ("unexpected-file", "notes.txt: unexpected file"),
]


@pytest.mark.parametrize(("name", "message"), BROKEN, ids=[n for n, _ in BROKEN])
def test_broken_fixture_fails(name, message, capsys):
    code, err = run(FIXTURES / name, capsys)
    assert code == 1
    assert message in err
    assert err.count("error:") == 1  # a minimal fixture breaks exactly one rule


def test_duplicate_id_across_files(tmp_path, capsys):
    root = tmp_path / "d"
    shutil.copytree(FIXTURES / "valid", root)
    shutil.copy(root / "key/v1/train.jsonl", root / "template/t.jsonl")
    code, err = run(root, capsys)
    assert code == 1 and "duplicate id 't-0001'" in err


def test_template_accepts_empty_text_but_key_does_not(capsys):
    assert run(FIXTURES / "valid", capsys)[0] == 0  # template row has empty text
    assert run(FIXTURES / "empty-text", capsys)[0] == 1


def test_validator_never_rewrites_files(tmp_path, capsys):
    root = tmp_path / "d"
    shutil.copytree(FIXTURES / "crlf", root)
    before = (root / "key/v1/train.jsonl").read_bytes()
    run(root, capsys)
    assert (root / "key/v1/train.jsonl").read_bytes() == before


def test_bidi_mark_and_joiners_are_accepted(tmp_path, capsys):
    root = tmp_path / "d"
    shutil.copytree(FIXTURES / "valid", root)
    path = root / "key/v1/train.jsonl"
    text = path.read_text("utf-8").replace("ببب", "ب‏ب‍ب‌ب", 1)
    path.write_text(text, encoding="utf-8", newline="")
    assert run(root, capsys) == (0, "")


def test_symlinked_file_is_rejected(tmp_path, capsys):
    root = tmp_path / "d"
    shutil.copytree(FIXTURES / "valid", root)
    real = tmp_path / "outside.jsonl"
    real.write_bytes((root / "key/v1/train.jsonl").read_bytes())
    (root / "key/v1/train.jsonl").unlink()
    (root / "key/v1/train.jsonl").symlink_to(real)
    code, err = run(root, capsys)
    assert code == 1 and "train.jsonl: symlinks are not allowed" in err


def test_symlinked_directory_resolving_outside_is_rejected(tmp_path, capsys):
    root = tmp_path / "d"
    shutil.copytree(FIXTURES / "valid", root)
    outside = tmp_path / "elsewhere"
    shutil.move(root / "template", outside)
    (root / "template").symlink_to(outside, target_is_directory=True)
    code, err = run(root, capsys)
    assert code == 1 and "resolves outside" in err


def test_byte_fixtures_keep_their_bytes():
    crlf = (FIXTURES / "crlf/key/v1/train.jsonl").read_bytes()
    bom = (FIXTURES / "bom/key/v1/train.jsonl").read_bytes()
    assert b"\r\n" in crlf
    assert bom.startswith(b"\xef\xbb\xbf")


def test_split_function_is_pinned():
    assert split_of("t-0001") == "train"
    assert split_of("t-0014") == "test"
    assert split_of("t-0017") == "test"
    assert split_of("t-0049") == "test"  # first sha256 byte 50, just under 51
    assert split_of("t-0059") == "train"  # first sha256 byte 52, just over 51


def test_arabic_letter_helper():
    assert has_arabic_letter("ببب") and not has_arabic_letter("x 123 ً")
