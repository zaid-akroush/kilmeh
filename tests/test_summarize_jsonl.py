import json
import shutil
from pathlib import Path

import pytest

from kilmeh.cli import main

FIXTURE = Path(__file__).parent / "fixtures" / "harbor_run"


@pytest.fixture
def jobs(tmp_path):
    shutil.copytree(FIXTURE, tmp_path / "jobs")
    return tmp_path / "jobs"


def records(jobs, out):
    assert main(["summarize-run", str(jobs), "--jsonl", str(out)]) == 0
    lines = out.read_text("utf-8").splitlines()
    return {r["trial_id"].split("__")[0]: r for r in map(json.loads, lines)}


def test_tokens_from_result_json(jobs, tmp_path):
    r = records(jobs, tmp_path / "o.jsonl")["pass-tokens"]
    assert r["schema_version"] == 1
    assert (r["task_id"], r["prompt_variant"]) == ("demo", "en")
    assert (r["agent"], r["model"]) == ("codex", "m1")
    assert (r["input_tokens"], r["cached_tokens"]) == (1000, 800)
    assert (r["output_tokens"], r["cost_usd"]) == (50, 0.5)
    assert (r["reward"], r["status"], r["duration_sec"]) == (1.0, "passed", 61.5)
    assert r["checks"] == {"a": True, "b": True}
    assert r["transcript"] == "job-1/pass-tokens__aaa/agent/trajectory.json"
    assert r["verify_log"] == "job-1/pass-tokens__aaa/verifier/verify.log"
    assert r["diff"] is None


def test_tokens_fall_back_to_trajectory(jobs, tmp_path):
    r = records(jobs, tmp_path / "o.jsonl")["fail-traj-tokens"]
    assert (r["input_tokens"], r["cached_tokens"]) == (200, 100)
    assert (r["output_tokens"], r["cost_usd"]) == (7, None)
    assert (r["status"], r["prompt_variant"], r["checks"]["b"]) == ("failed", "levantine", False)


def test_absent_tokens_checks_and_transcript_are_null(jobs, tmp_path):
    r = records(jobs, tmp_path / "o.jsonl")["fail-no-tokens"]
    for k in ("input_tokens", "cached_tokens", "output_tokens", "cost_usd", "checks", "transcript"):
        assert r[k] is None
    assert r["status"] == "failed"


def test_timeout_trial_keeps_its_reward(jobs, tmp_path):
    r = records(jobs, tmp_path / "o.jsonl")["timeout"]
    assert (r["status"], r["reward"], r["duration_sec"]) == ("timeout", 0.0, 600.5)


def test_error_trial_has_no_reward(jobs, tmp_path):
    r = records(jobs, tmp_path / "o.jsonl")["error"]
    assert (r["status"], r["reward"], r["checks"]) == ("error", None, None)


def test_table_unchanged_by_jsonl(jobs, tmp_path, capsys):
    main(["summarize-run", str(jobs)])
    plain = capsys.readouterr().out
    main(["summarize-run", str(jobs), "--jsonl", str(tmp_path / "o.jsonl")])
    assert capsys.readouterr().out == plain


def test_leak_refusal_writes_no_file(jobs, tmp_path, capsys):
    log = jobs / "job-1" / "error__eee" / "verifier" / "verify.log"
    log.write_text("sk-ant-api03-" + "b" * 30, encoding="utf-8")
    out = tmp_path / "o.jsonl"
    assert main(["summarize-run", str(jobs), "--jsonl", str(out)]) == 2
    assert not out.exists()
    assert capsys.readouterr().out == ""


def test_timeout_with_reward_one_is_status_timeout_but_counted_passed(jobs, tmp_path, capsys):
    (jobs / "job-1" / "timeout__ddd" / "verifier" / "reward.txt").write_text("1", encoding="utf-8")
    r = records(jobs, tmp_path / "o.jsonl")["timeout"]
    assert (r["status"], r["reward"]) == ("timeout", 1.0)
    main(["summarize-run", str(jobs)])
    assert "| demo--en | codex/m1 | 4 | 1 | 1 | 2 | 67% |" in capsys.readouterr().out
