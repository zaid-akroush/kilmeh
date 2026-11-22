"""Shared helpers for the Track B task tests (tests/test_b_*.py).

Host runs use KILMEH_APP to point a task's verify.py and solve.sh at a temp copy of the fixture
(like tests/test_seed_task_001.py). `run_in_image` runs a shell script in the task's image with
the network off, for the cases that need the real container (uid drop, reward.txt, daemons).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from kilmeh import selftest

ROOT = Path(__file__).resolve().parent.parent
TRACK = ROOT / "tasks" / "b-arabic-in-code"


def task_dir(task_id: str) -> Path:
    return TRACK / task_id


def fresh_app(task: Path, tmp: Path) -> Path:
    app = tmp / "app"
    shutil.copytree(task / "fixture", app)
    return app


def apply(script: Path, app: Path) -> None:
    """Apply a solution directory (its solve.sh) or a QA script (.py, run in the app dir)."""
    env = dict(os.environ, KILMEH_APP=str(app))
    if script.is_dir():
        cmd = ["bash", str(script / "solve.sh")]
    else:
        cmd = [sys.executable, "-I", str(script)]
    subprocess.run(cmd, cwd=app, env=env, check=True, capture_output=True, timeout=60)


def run_verify_raw(task: Path, app: Path, lock: bool = True) -> subprocess.CompletedProcess:
    """Run the task's verify.py the way test.sh does (python -I -S) against `app`, from a copy of
    tests/. With `lock`, the copy gets no group/other access, as test.sh does in the container
    (Track B graders refuse to run otherwise)."""
    env = dict(os.environ, KILMEH_APP=str(app))
    with tempfile.TemporaryDirectory() as scratch:
        tests = Path(scratch) / "tests"
        shutil.copytree(task / "tests", tests)
        os.chmod(scratch, 0o700)
        if lock:
            for path in [tests, *tests.rglob("*")]:
                path.chmod(path.stat().st_mode & 0o700)
        else:
            for path in [tests, *tests.rglob("*")]:
                path.chmod(path.stat().st_mode | 0o044 | (0o011 if path.is_dir() else 0))
        mjs = tests / "verify.mjs"  # a JavaScript task: node, not python
        cmd = [sys.executable, "-I", "-S", str(tests / "verify.py")]
        return subprocess.run(
            ["node", str(mjs)] if mjs.exists() else cmd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )


def run_verify(task: Path, app: Path) -> tuple[int, dict[str, bool]]:
    proc = run_verify_raw(task, app)
    return proc.returncode, json.loads(proc.stdout)


def failing(result: dict[str, bool]) -> set[str]:
    return {k for k, v in result.items() if not v}


def check_lines(stderr: str) -> list[tuple[str, str]]:
    """(PASS or FAIL, key) for each `PASS key: detail` / `FAIL key: detail` line on stderr."""
    return [(m[1], m[2]) for m in re.finditer(r"^(PASS|FAIL) (\w+): \S", stderr, re.MULTILINE)]


def run_in_image(task: Path, script: str, mounts: dict[Path, str], timeout: int = 300) -> str:
    """Build the task image, run `script` with bash in it, and return its stdout. tests/ is
    copied in as a writable /tests (like the self-test's grader phase and Harbor); `mounts`
    (host path -> container path) are read-only binds."""
    task = task.resolve()
    tag = f"kilmeh-btest-{task.name}"
    build = subprocess.run(
        selftest.build_command(task, tag), capture_output=True, text=True, timeout=600
    )
    assert build.returncode == 0, "docker build failed: " + (build.stdout + build.stderr)[-800:]
    name = f"{tag}-{time.time_ns()}"
    cmd = ["docker", "create", "--name", name, "--network", "none"]
    for host, inside in mounts.items():
        cmd += ["-v", f"{host.resolve()}:{inside}:ro"]
    cmd += ["-w", "/app", tag, "bash", "-c", script]
    try:
        subprocess.run(cmd, capture_output=True, check=True, timeout=120)
        subprocess.run(
            selftest.tests_copy_command(task, name), capture_output=True, check=True, timeout=120
        )
        done = subprocess.run(
            ["docker", "start", "-a", name], capture_output=True, text=True, timeout=timeout
        )
        return done.stdout
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=60)
