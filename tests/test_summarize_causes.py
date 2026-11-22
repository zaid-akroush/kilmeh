import json
from pathlib import Path

from kilmeh.cli import main
from kilmeh.summarize import records


def trial(jobs: Path, name: str, variant: str, reward: str | None, exc: str | None = None):
    d = jobs / "job-1" / name
    (d / "verifier").mkdir(parents=True)
    result = {
        "task_name": f"kilmeh/t--{variant}",
        "trial_name": name,
        "agent_info": {"name": "codex", "model_info": {"name": "m"}},
        "exception_info": exc and {"exception_type": exc, "exception_message": "x"},
    }
    (d / "result.json").write_text(json.dumps(result), encoding="utf-8")
    if reward is not None:
        (d / "verifier" / "reward.txt").write_text(reward, encoding="utf-8")


def cause_of(tmp_path, reward, exc=None):
    trial(tmp_path, "t", "en", reward, exc)
    return records(tmp_path)[0]["failure_cause"]


def test_setup_timeout(tmp_path):
    assert cause_of(tmp_path, None, "AgentSetupTimeoutError") == "setup_timeout"


def test_environment_build_error_is_setup_timeout(tmp_path):
    assert cause_of(tmp_path, None, "DockerBuildError") == "setup_timeout"


def test_agent_timeout(tmp_path):
    assert cause_of(tmp_path, "0", "AgentTimeoutError") == "agent_timeout"


def test_harness_error(tmp_path):
    assert cause_of(tmp_path, None, "NonZeroAgentExitCodeError") == "harness_error"


def test_missing_reward_without_exception_is_harness_error(tmp_path):
    assert cause_of(tmp_path, None) == "harness_error"


def test_tests_failed(tmp_path):
    assert cause_of(tmp_path, "0") == "tests_failed"


def test_timed_out_pass_has_no_cause_but_is_counted(tmp_path, capsys):
    trial(tmp_path, "t1", "en", "1", "AgentTimeoutError")
    assert records(tmp_path)[0]["failure_cause"] is None
    main(["summarize-run", str(tmp_path)])
    assert "| codex/m | en | 1 | 0 | 0 | 0 | 0 |" in capsys.readouterr().out


def test_failure_causes_table_rows(tmp_path, capsys):
    trial(tmp_path, "t1", "en", "0")
    trial(tmp_path, "t2", "levantine", "0", "AgentTimeoutError")
    trial(tmp_path, "t3", "levantine", None, "AgentSetupTimeoutError")
    main(["summarize-run", str(tmp_path)])
    out = capsys.readouterr().out
    assert "| agent | variant | timed out | setup_timeout | agent_timeout |" in out
    assert "| codex/m | en | 0 | 0 | 0 | 0 | 1 |" in out
    assert "| codex/m | levantine | 1 | 1 | 1 | 0 | 0 |" in out


def test_existing_tables_unchanged(tmp_path, capsys):
    trial(tmp_path, "t1", "en", "1")
    trial(tmp_path, "t2", "levantine", "0")
    main(["summarize-run", str(tmp_path)])
    out = capsys.readouterr().out
    expected = (
        "| task variant | agent | trials | errors | timeouts | passed | pass rate | 95% CI |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| t--en | codex/m | 1 | 0 | 0 | 1 | 100% | 21–100% |\n"
        "| t--levantine | codex/m | 1 | 0 | 0 | 0 | 0% | 0–79% |\n"
        "\n## loop-for-to-while: English vs Levantine vs Arabizi\n\n"
        "| agent | en | levantine | arabizi_levantine |\n"
        "|---|---|---|---|\n"
        "| codex/m | - | - | - |\n"
        "\n## Parity vs English (pass rate / en pass rate)\n\n"
        "| agent | task variant | parity |\n"
        "|---|---|---|\n"
        "| codex/m | t--levantine | 0.00 |\n"
        "\n## Parity vs English per track (pooled)\n\n"
        "| agent | track | parity |\n"
        "|---|---|---|\n"
        "| codex/m | unknown | 0.00 |\n"
        "\n## Paired vs English (Track A)\n\n"
        "| agent | variant | both pass | en only | variant only | both fail | tasks | McNemar p |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "\n## Failure causes\n"
    )
    assert out.startswith(expected)
