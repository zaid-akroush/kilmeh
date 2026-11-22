import html
import json
import re
from pathlib import Path

from kilmeh.cli import main
from kilmeh.results_page import CAVEAT, render
from kilmeh.summarize import _wilson


def trial(jobs, name, variant, reward, agent="codex", started="2026-11-20T10:00:00"):
    d = jobs / "job-1" / name
    (d / "verifier").mkdir(parents=True)
    result = {
        "task_name": f"kilmeh/{variant}",
        "trial_name": name,
        "started_at": started,
        "agent_info": {"name": agent, "model_info": {"name": "m"}},
        "exception_info": None,
    }
    (d / "result.json").write_text(json.dumps(result), encoding="utf-8")
    (d / "verifier" / "reward.txt").write_text(reward, encoding="utf-8")


def fixture(root: Path, task="t") -> Path:
    for i, r in enumerate("110"):
        trial(root, f"a{i}", f"{task}--en", r)
    trial(root, "b0", f"{task}--levantine", "0")
    trial(root, "b1", f"{task}--levantine", "1")
    return root


def page(roots, tmp_path, **kw):
    return render(roots, tmp_path / "no-tasks", **kw)


def test_sections_and_header(tmp_path):
    h = page([fixture(tmp_path)], tmp_path)
    assert h.startswith("<!doctype html>") and '<html lang="en">' in h
    assert CAVEAT in h and "2026-11-20 to 2026-11-20" in h and "codex/m" in h
    for s in ("Overall", "Per track", "Per task", "Track A", "Failure causes"):
        assert f"<h2>{s}" in h
    assert "prefers-color-scheme:dark" in h and "viewport" in h


def test_numbers_match_summarize(tmp_path):
    h = page([fixture(tmp_path)], tmp_path)
    assert "2/3 (67%, CI " + _wilson(2, 3) + ")" in h
    assert "<td>3</td><td>5</td><td>60%</td><td>" + _wilson(3, 5) + "</td>" in h


def test_escapes_task_name(tmp_path):
    h = page([fixture(tmp_path, task="<script>x</script>")], tmp_path, title="<b>T</b>")
    assert "<script>" not in h and "&lt;script&gt;x&lt;/script&gt;" in h
    assert "<b>T</b>" not in h


def test_no_external_urls(tmp_path):
    h = page([fixture(tmp_path)], tmp_path)
    assert "http" not in h and not re.search(r"<(script|link|img|iframe)\b", h)


def test_arabic_cell_has_dir_auto(tmp_path):
    h = page([fixture(tmp_path, task="كلمة")], tmp_path)
    assert '<td dir="auto">كلمة</td>' in h
    assert '<td dir="auto">t</td>' not in h


def test_two_jobs_dirs_two_rows(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    trial(a, "x", "t--en", "1", agent="claude-code")
    trial(b, "y", "t--en", "0", agent="codex")
    h = page([a, b], tmp_path)
    assert h.count("<td>claude-code/m</td><td>1</td>") == 1
    assert h.count("<td>codex/m</td><td>0</td>") == 1


def test_cli_writes_file_utf8(tmp_path):
    out = tmp_path / "o.html"
    jobs = fixture(tmp_path / "jobs")
    assert main(["results-page", str(out), str(jobs), "--tasks", str(tmp_path)]) == 0
    assert "<title>Kilmeh results</title>" in out.read_text(encoding="utf-8")


def test_overall_ci_differs_from_per_track(tmp_path):
    tasks = tmp_path / "tasks"
    (tasks / "a-prompts" / "t1").mkdir(parents=True)
    (tasks / "b-arabic-in-code" / "t2").mkdir(parents=True)
    jobs = tmp_path / "jobs"
    for i in range(3):
        trial(jobs, f"p{i}", "t1--en", "1")
    for i in range(2):
        trial(jobs, f"f{i}", "t2--en", "0")
    h = render([jobs], tasks)
    overall = h.split("<h2>Per track")[0]
    assert f"<td>3</td><td>5</td><td>60%</td><td>{_wilson(3, 5)}</td>" in overall
    assert _wilson(3, 3) != _wilson(3, 5) and _wilson(3, 3) not in overall
    assert f"<td>3</td><td>3</td><td>100%</td><td>{_wilson(3, 3)}</td>" in h


def test_hostile_strings_escaped_in_headers_and_agents(tmp_path):
    bad = "<script>x</script>\"'"
    trial(tmp_path, "x", f"t--{bad}", "1", agent=bad)
    h = page([tmp_path], tmp_path)
    esc = html.escape(bad)
    assert "<script>" not in h and bad not in h
    assert f"<th>{esc}</th>" in h
    assert f"Agents and models: {esc}/m." in h
    assert re.findall(r"<h2>([^<]*)</h2>", h)[0] == "Overall pass rate per agent"
