import pytest

from kilmeh.cli import main
from kilmeh.summarize import _mcnemar, _wilson
from test_summarize_run import trial


def test_wilson_zero_of_one():
    assert _wilson(0, 1) == "0–79%"


def test_wilson_one_of_one():
    assert _wilson(1, 1) == "21–100%"


def test_wilson_three_of_ten():
    # hand: centre 0.3555, half-width 0.2477 -> 10.8% to 60.3%
    assert _wilson(3, 10) == "11–60%"


def test_wilson_no_graded_trials():
    assert _wilson(0, 0) == "-"


def test_mcnemar_zero_four():
    assert _mcnemar(0, 4) == pytest.approx(0.125)


def test_mcnemar_symmetric_and_balanced():
    assert _mcnemar(4, 0) == _mcnemar(0, 4)
    assert _mcnemar(2, 2) == 1.0
    assert _mcnemar(0, 0) == 1.0


def paired(capsys, tmp_path, specs):
    """specs: (task variant, reward) per trial, one agent; tasks live under a-prompts."""
    j = tmp_path / "jobs"
    tasks = tmp_path / "tasks"
    for i, (variant, reward) in enumerate(specs):
        trial(j, f"t{i}", variant, "codex", "m", reward)
        (tasks / "a-prompts" / variant.partition("--")[0]).mkdir(parents=True, exist_ok=True)
    main(["summarize-run", str(j), "--tasks", str(tasks)])
    return capsys.readouterr().out


def test_pairing_counts(capsys, tmp_path):
    out = paired(
        capsys,
        tmp_path,
        [
            ("a--en", "1"), ("a--msa", "1"),  # both pass
            ("b--en", "1"), ("b--msa", "0"),  # en only
            ("c--en", "0"), ("c--msa", "1"),  # variant only
            ("d--en", "0"), ("d--msa", "0"),  # both fail
            ("e--en", "1"), ("e--msa", "0"),  # en only
        ],
    )  # fmt: skip
    assert "| codex/m | msa | 1 | 2 | 1 | 1 | 5 | 1.000 |" in out
    assert "| codex/m | all | 1 | 2 | 1 | 1 | 5 | - |" in out


def test_pairing_majority_over_tries(capsys, tmp_path):
    out = paired(
        capsys,
        tmp_path,
        [
            ("a--en", "1"),
            ("a--en", "1"),
            ("a--en", "0"),
            ("a--msa", "0"),
            ("a--msa", "0"),
            ("a--msa", "1"),
        ],
    )
    assert "| codex/m | msa | 0 | 1 | 0 | 0 | 1 | 1.000 |" in out


def test_pairing_pools_variant_kinds(capsys, tmp_path):
    out = paired(
        capsys,
        tmp_path,
        [("a--en", "1"), ("a--msa", "0"), ("a--levantine", "0"), ("b--en", "1"), ("b--msa", "0")],
    )
    assert "| codex/m | levantine | 0 | 1 | 0 | 0 | 1 |" in out
    assert "| codex/m | msa | 0 | 2 | 0 | 0 | 2 |" in out
    assert "| codex/m | all | 0 | 3 | 0 | 0 | 3 | - |" in out


def test_pooled_row_has_no_p_value(capsys, tmp_path):
    out = paired(capsys, tmp_path, [("a--en", "1"), ("a--msa", "0"), ("a--levantine", "0")])
    assert "| codex/m | msa | 0 | 1 | 0 | 0 | 1 | 1.000 |" in out
    assert [ln for ln in out.splitlines() if "| all |" in ln][0].endswith("| 2 | - |")


def test_pairing_skips_other_tracks_and_missing_en(capsys, tmp_path):
    j = tmp_path / "jobs"
    trial(j, "t1", "x--en", "codex", "m", "1")
    trial(j, "t2", "x--msa", "codex", "m", "0")  # task not under a-prompts
    trial(j, "t3", "y--msa", "codex", "m", "0")  # no en variant
    (tmp_path / "tasks" / "a-prompts" / "y").mkdir(parents=True)
    main(["summarize-run", str(j), "--tasks", str(tmp_path / "tasks")])
    out = capsys.readouterr().out
    assert out.split("## Paired vs English (Track A)")[1].split("##")[0].count("codex/m") == 0


def test_paired_table_header_and_order(capsys, tmp_path):
    out = paired(capsys, tmp_path, [("a--en", "1"), ("a--msa", "1")])
    assert out.index("## Parity vs English per track") < out.index("## Paired vs English")
    assert out.index("## Paired vs English") < out.index("## Failure causes")
    assert "| both pass | en only | variant only | both fail | tasks | McNemar p |" in out


def test_en_tie_counts_as_fail(capsys, tmp_path):
    out = paired(
        capsys, tmp_path, [("a--en", "1"), ("a--en", "0"), ("a--msa", "1"), ("a--msa", "1")]
    )
    assert "| codex/m | msa | 0 | 0 | 1 | 0 | 1 | 1.000 |" in out


def test_variant_tie_counts_as_fail(capsys, tmp_path):
    out = paired(
        capsys, tmp_path, [("a--en", "1"), ("a--en", "1"), ("a--msa", "1"), ("a--msa", "0")]
    )
    assert "| codex/m | msa | 0 | 1 | 0 | 0 | 1 | 1.000 |" in out


def test_stdout_is_utf8_even_when_console_is_cp1252(tmp_path, monkeypatch):
    import io
    import sys

    j = tmp_path / "jobs"
    trial(j, "t1", "x--en", "codex", "m", "1")
    raw = io.BytesIO()
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(raw, encoding="cp1252"))
    main(["summarize-run", str(j), "--tasks", str(tmp_path / "tasks")])
    sys.stdout.flush()
    assert "21–100%".encode() in raw.getvalue()
