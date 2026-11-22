"""Pin the per-check log lines of the Track B graders: `PASS|FAIL <key>: <DETAIL[key]>` exactly.

Agents can read verify.log, so the detail must be each verify.py's fixed DETAIL text, never an
input or expected value. Linux only (the graders call `os.geteuid`), like the other test_b_* files.
"""

import ast
import json
import re

import pytest

from b_helpers import apply, fresh_app, run_verify_raw, task_dir

TASKS = [
    "arabic-digits-parse-format",
    "arabic-search-normalize",
    "arabic-bytes-survive-edit",
    "arabic-file-io",
    "jod-currency-format",
]


def detail_of(task) -> dict[str, str]:
    mjs = task / "tests" / "verify.mjs"
    if mjs.exists():  # `const DETAIL = {...};` is written as JSON
        return json.loads(
            re.search(r"const DETAIL = (\{.*?\n\});", mjs.read_text("utf-8"), re.S)[1]
        )
    tree = ast.parse((task / "tests" / "verify.py").read_text("utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "DETAIL":
            return ast.literal_eval(node.value)
    raise AssertionError("no DETAIL in verify.py")


@pytest.mark.parametrize("solution", ["reference", "known-bad", None])
@pytest.mark.parametrize("task_id", TASKS)
def test_log_lines_are_fixed_detail(task_id, solution, tmp_path):
    task = task_dir(task_id)
    detail = detail_of(task)
    app = fresh_app(task, tmp_path)
    if solution:
        apply(task / "solutions" / solution, app)
    proc = run_verify_raw(task, app)
    lines = proc.stderr.splitlines()
    keys = []
    for line in lines:
        m = re.fullmatch(r"(PASS|FAIL) (\w+): (.*)", line)
        if not m:
            continue
        keys.append(m[2])
        # FAIL lines read "expected <DETAIL>" today (reported to the CTO); nothing else is allowed.
        want = detail[m[2]] if m[1] == "PASS" else f"expected {detail[m[2]]}"
        assert line == f"{m[1]} {m[2]}: {want}", line
    assert keys and set(keys) == set(detail) and len(keys) == len(detail)
