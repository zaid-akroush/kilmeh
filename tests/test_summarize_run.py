import json
from pathlib import Path

import pytest

from kilmeh.cli import main

# Checksum-shaped hex and long paths appear in real Harbor result.json files; never a token.
SHA = "3f" * 32


def trial(
    jobs: Path,
    name: str,
    task: str,
    agent: str,
    model: str,
    reward: str | None,
    exception: str | None = None,
):
    d = jobs / "job-1" / name
    (d / "verifier").mkdir(parents=True)
    (d / "agent").mkdir()
    result = {
        "task_name": f"kilmeh/{task}",
        "trial_name": name,
        "trial_uri": f"file:///D:/kilmeh-runs/jobs/job-1/{name}/with/a/long/path/segment",
        "task_checksum": SHA,
        "agent_info": {"name": agent, "version": "1.0", "model_info": {"name": model}},
        "exception_info": exception and {"exception_type": exception, "exception_message": "x"},
    }
    (d / "result.json").write_text(json.dumps(result), encoding="utf-8")
    (d / "config.json").write_text("{}", encoding="utf-8")
    if reward is not None:
        (d / "verifier" / "reward.txt").write_text(reward, encoding="utf-8")
    return d


@pytest.fixture
def jobs(tmp_path):
    j = tmp_path / "jobs"
    trial(j, "t1", "loop-for-to-while--en", "codex", "m1", "1")
    trial(j, "t2", "loop-for-to-while--en", "codex", "m1", "0")
    trial(j, "t3", "loop-for-to-while--levantine", "codex", "m1", "1")
    trial(j, "t4", "loop-for-to-while--arabizi_levantine", "codex", "m1", None)
    trial(j, "t5", "rtl-nav-fix--en", "claude-code", "m2", "1.0")
    return j


def run(capsys, jobs, *extra):
    code = main(["summarize-run", str(jobs), *extra])
    out, err = capsys.readouterr()
    return code, out, err


def test_pass_rate_per_variant_and_agent(capsys, jobs):
    code, out, _ = run(capsys, jobs)
    assert code == 0
    assert "| loop-for-to-while--en | codex/m1 | 2 | 0 | 0 | 1 | 50% |" in out
    assert "| rtl-nav-fix--en | claude-code/m2 | 1 | 0 | 0 | 1 | 100% |" in out


def test_trial_without_reward_counts_as_fail(capsys, jobs):
    _, out, _ = run(capsys, jobs)
    assert "| loop-for-to-while--arabizi_levantine | codex/m1 | 1 | 0 | 0 | 0 | 0% |" in out


def test_harbor_exception_is_an_error_not_a_fail(capsys, jobs):
    trial(jobs, "t6", "loop-for-to-while--en", "codex", "m1", None, "NetworkConnectionError")
    _, out, _ = run(capsys, jobs)
    # 3 trials, 1 errored: rate is 1 passed of 2 graded
    assert "| loop-for-to-while--en | codex/m1 | 3 | 1 | 0 | 1 | 50% |" in out
    assert "| codex/m1 | 1/2 | 1/1 | 0/1 |" in out


def test_all_errored_has_no_rate(capsys, jobs):
    trial(jobs, "t6", "rtl-nav-fix--levantine", "codex", "m1", None, "NetworkConnectionError")
    _, out, _ = run(capsys, jobs)
    assert "| rtl-nav-fix--levantine | codex/m1 | 1 | 1 | 0 | 0 | - |" in out


def test_header_has_timeouts_column(capsys, jobs):
    _, out, _ = run(capsys, jobs)
    assert "| task variant | agent | trials | errors | timeouts | passed | pass rate |" in out


def test_timeout_with_reward_is_graded_and_counted_as_timeout(capsys, jobs):
    # the verifier still ran, so the reward stands; the timeouts column is informational
    trial(jobs, "t6", "rtl-nav-fix--levantine", "codex", "m1", "0", "AgentTimeoutError")
    trial(jobs, "t7", "rtl-nav-fix--levantine", "codex", "m1", "1", "AgentTimeoutError")
    _, out, _ = run(capsys, jobs)
    assert "| rtl-nav-fix--levantine | codex/m1 | 2 | 0 | 2 | 1 | 50% |" in out


def test_timeout_without_reward_is_an_error_not_a_timeout(capsys, jobs):
    trial(jobs, "t6", "rtl-nav-fix--levantine", "codex", "m1", None, "AgentTimeoutError")
    _, out, _ = run(capsys, jobs)
    assert "| rtl-nav-fix--levantine | codex/m1 | 1 | 1 | 0 | 0 | - |" in out


def test_other_exception_with_reward_is_graded_not_a_timeout(capsys, jobs):
    trial(jobs, "t6", "rtl-nav-fix--levantine", "codex", "m1", "1", "VerifierTimeoutError")
    _, out, _ = run(capsys, jobs)
    assert "| rtl-nav-fix--levantine | codex/m1 | 1 | 0 | 0 | 1 | 100% |" in out


def test_rate_rounds_half_up(capsys, tmp_path):
    j = tmp_path / "jobs"
    for i in range(8):  # 1/8 = 12.5%: half-up gives 13, banker's round gives 12
        trial(j, f"t{i}", "rtl-nav-fix--en", "codex", "m1", "1" if i == 0 else "0")
    _, out, _ = run(capsys, j)
    assert "| rtl-nav-fix--en | codex/m1 | 8 | 0 | 0 | 1 | 13% |" in out


def test_loop_language_comparison(capsys, jobs):
    _, out, _ = run(capsys, jobs)
    assert "| agent | en | levantine | arabizi_levantine |" in out
    assert "| codex/m1 | 1/2 | 1/1 | 0/1 |" in out
    # an agent with no loop trials still gets a row, with dashes
    assert "| claude-code/m2 | - | - | - |" in out


def test_no_trials_is_an_error(capsys, tmp_path):
    code, out, err = run(capsys, tmp_path)
    assert code == 2
    assert out == ""
    assert "no trials" in err


def assert_leak_caught(capsys, jobs, leak: str, kind: str):
    log = jobs / "job-1" / "t1" / "agent" / "codex.txt"
    log.write_text(f"some output {leak} more output", encoding="utf-8")
    code, out, err = run(capsys, jobs)
    assert code == 2
    assert out == ""
    assert "codex.txt" in err
    assert kind in err  # this specific pattern fired, not just a broader one
    assert leak not in err  # never echo the secret itself


def test_scan_catches_anthropic_api_key(capsys, jobs):
    assert_leak_caught(capsys, jobs, "sk-ant-api03-" + "b" * 30, "anthropic key or OAuth token")


def test_scan_catches_claude_code_oauth_token(capsys, jobs):
    assert_leak_caught(capsys, jobs, "sk-ant-oat01-" + "a" * 30, "anthropic key or OAuth token")


def test_scan_catches_openai_style_sk_key(capsys, jobs):
    assert_leak_caught(capsys, jobs, "sk-proj-" + "c1D2" * 8, "sk- key")


def test_scan_catches_lowercase_hex_sk_key(capsys, jobs):
    assert_leak_caught(capsys, jobs, "sk-" + "0123456789abcdef" * 2, "lowercase-hex sk- key")


def test_scan_catches_hugging_face_token(capsys, jobs):
    # 37 chars: too short for the long-base64 check, so only the hf_ pattern can catch it
    assert_leak_caught(capsys, jobs, "hf_aBcDeFgHiJkLmNoPqRsTuVwXyZ01234567", "Hugging Face token")


def test_scan_catches_jwt(capsys, jobs):
    assert_leak_caught(capsys, jobs, "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.sig", "JWT")


def test_scan_catches_long_base64(capsys, jobs):
    blob = "QWxhZGRpbjpvcGVuIHNlc2FtZQ9Xk2mPq7LrT4vZ8bN3cY6"
    assert_leak_caught(capsys, jobs, blob, "long base64")


def test_scan_catches_json_escaped_slashes(capsys, jobs):
    # each `\/`-separated piece is under 40 chars; only the joined run is long enough
    assert_leak_caught(
        capsys, jobs, r"QWxhZGRpbjpvcGVu\/IHNlc2FtZQ9Xk2mP\/q7LrT4vZ8bN3cY6", "long base64"
    )


def test_scan_ignores_hex_checksums_and_paths(capsys, jobs):
    (jobs / "job-1" / "t1" / "agent" / "notes.txt").write_text(
        f"{SHA} D:/kilmeh-runs/harbor-tasks/loop-for-to-while--arabizi_levantine/tests",
        encoding="utf-8",
    )
    code, _, _ = run(capsys, jobs)
    assert code == 0


def test_parity_per_variant(capsys, jobs):
    _, out, _ = run(capsys, jobs)
    # en 1/2 = 50%; levantine 1/1 = 100% -> 2.00; arabizi 0/1 -> 0.00
    assert "| codex/m1 | loop-for-to-while--levantine | 2.00 |" in out
    assert "| codex/m1 | loop-for-to-while--arabizi_levantine | 0.00 |" in out


def test_parity_dash_when_en_rate_zero(capsys, jobs):
    trial(jobs, "t6", "rtl-nav-fix--en", "codex", "m1", "0")
    trial(jobs, "t7", "rtl-nav-fix--msa", "codex", "m1", "1")
    _, out, _ = run(capsys, jobs)
    assert "| codex/m1 | rtl-nav-fix--msa | - |" in out


def test_parity_excludes_errors(capsys, jobs):
    # an errored en trial must not lower the en rate (1/3 would give 3.00)
    trial(jobs, "t6", "loop-for-to-while--en", "codex", "m1", None, "NetworkConnectionError")
    _, out, _ = run(capsys, jobs)
    assert "| codex/m1 | loop-for-to-while--levantine | 2.00 |" in out


def test_parity_per_track_is_pooled(capsys, jobs, tmp_path):
    tasks = tmp_path / "tasks"
    (tasks / "a-prompts" / "loop-for-to-while").mkdir(parents=True)
    (tasks / "a-prompts" / "other").mkdir()
    trial(jobs, "t6", "other--en", "codex", "m1", "1")
    trial(jobs, "t7", "other--msa", "codex", "m1", "0")
    _, out, _ = run(capsys, jobs, "--tasks", str(tasks))
    # non-en 1/3 over en 2/3 = 0.50 (a mean of per-variant ratios would be 0.67)
    assert "| codex/m1 | a-prompts | 0.50 |" in out


def test_parity_unknown_track(capsys, jobs, tmp_path):
    _, out, _ = run(capsys, jobs, "--tasks", str(tmp_path / "no-tasks"))
    # non-en 1/2 over en 1/2
    assert "| codex/m1 | unknown | 1.00 |" in out


def test_parity_rounds_half_up(capsys, tmp_path):
    j = tmp_path / "jobs"
    trial(j, "e0", "rtl-nav-fix--en", "codex", "m1", "1")
    for i in range(8):  # 1/8 = 0.125: half-up gives 0.13, round() gives 0.12
        trial(j, f"t{i}", "rtl-nav-fix--msa", "codex", "m1", "1" if i == 0 else "0")
    _, out, _ = run(capsys, j)
    assert "| codex/m1 | rtl-nav-fix--msa | 0.13 |" in out


# 41-char Harbor trial dir name with upper, lower and digit: base64-shaped, but not a secret
TRIAL_DIR = "loop-for-to-while--arabizi_levan__nuJgXM4"


def trial_with_note(jobs: Path, note: str) -> Path:
    d = trial(jobs, TRIAL_DIR, "loop-for-to-while--arabizi_levantine", "codex", "m1", "0")
    r = json.loads((d / "result.json").read_text(encoding="utf-8"))
    r["note"] = note
    (d / "result.json").write_text(json.dumps(r), encoding="utf-8")
    return d


def test_scan_ignores_trial_dir_names(capsys, jobs):
    trial_with_note(jobs, f"/jobs/{TRIAL_DIR}/trial.log")
    code, _, err = run(capsys, jobs)
    assert code == 0, err


def test_scan_still_catches_base64_beside_a_trial_dir_name(capsys, jobs):
    trial_with_note(jobs, f"{TRIAL_DIR} QWxhZGRpbjpvcGVuIHNlc2FtZQ9Xk2mPq7LrT4vZ8bN3cY6")
    code, out, err = run(capsys, jobs)
    assert code == 2
    assert out == ""
    assert f"{Path(TRIAL_DIR, 'result.json')}: long base64" in err


def test_scan_blanked_name_does_not_join_its_neighbours(capsys, jobs):
    # json.dumps keeps `/` as is, so write the JSON-escaped `\/` form by hand
    d = trial_with_note(jobs, "")
    # 20 chars each: alone too short to flag, 44 if joined as `a\/\/b`
    halves = "QWxhZGRpbjpvcGVuIHNl", "c2FtZQ9Xk2mPq7LrT4vZ"
    raw = (d / "result.json").read_text(encoding="utf-8")
    note = f"{halves[0]}\\/{TRIAL_DIR}\\/{halves[1]}"
    (d / "result.json").write_text(raw.replace('"note": ""', f'"note": "{note}"'), encoding="utf-8")
    code, _, err = run(capsys, jobs)
    assert code == 0, err


def test_scan_does_not_blank_short_names(capsys, jobs):
    # codex writes sessions/2026/11/14/; blanking `11` would cut this blob into short pieces
    (jobs / "job-1" / "t1" / "agent" / "11").mkdir()
    assert_leak_caught(capsys, jobs, "QWxhZGRpbjpvcGVuIHNl11c2FtZQ9Xk2mPq7LrT4vZ", "long base64")
