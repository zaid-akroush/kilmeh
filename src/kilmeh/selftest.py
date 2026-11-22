"""Prove each task in Docker: reference passes, known-bad fails, untouched fixture fails.

Follows the run contract in tasks/SCHEMA.md. Docker is called with argument lists only.
One container runs twice, like Harbor: first it applies the solution with no /tests present;
then the host copies tests/ in (a writable copy the grader may lock down) and starts it again to
run the grader. The reward never travels over the container's stdout: after the container stops,
the host reads /logs/verifier/reward.txt out of it with `docker cp`, which nothing inside the
container can write.
"""

import io
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from kilmeh.tasks.validate import find_task_dirs, load_task

BUILD_TIMEOUT_SECONDS = 600
CP_TIMEOUT_SECONDS = 60
DETAIL_TAIL_CHARS = 400
REWARD_PATH = "/logs/verifier/reward.txt"

# First start (no /tests yet): apply the solution if one is mounted. Second start (the host has
# copied tests/ in): run the grader. Exit codes and output are ignored.
SCRIPT = (
    "if [ ! -e /tests ]; then "
    "if [ -f /solution/solve.sh ]; then bash /solution/solve.sh >/dev/null 2>&1; fi; "
    "else bash /tests/{entry} >/dev/null 2>&1; fi"
)

# reward.txt must hold exactly "1" or "0", optionally followed by one LF (what `echo 1 >` writes).
_ACCEPTED = {b"1": 1, b"0": 0, b"1\n": 1, b"0\n": 0}
_MAX_REWARD_BYTES = 2


@dataclass(frozen=True)
class RunResult:
    reward: int | None  # 1, 0, or None (no valid reward, timeout, docker error)
    detail: str  # short reason or tail of output


Runner = Callable[[Path, Path | None, int], RunResult]  # (task_dir, solution_dir, timeout)


@dataclass(frozen=True)
class SelfTestResult:
    task_id: str
    reference: RunResult
    known_bad: RunResult
    untouched: RunResult

    @property
    def ok(self) -> bool:
        return (
            self.reference.reward == 1 and self.known_bad.reward == 0 and self.untouched.reward == 0
        )


def parse_reward_tar(data: bytes) -> int | None:
    """Read the tar stream of `docker cp`. Accept one regular file named reward.txt of at most
    two bytes holding exactly 1 or 0 (plus one optional LF). Anything else is None."""
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as tf:
            members = tf.getmembers()
            if len(members) != 1:
                return None
            (member,) = members
            if member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE):
                return None
            if member.name != "reward.txt" or member.size > _MAX_REWARD_BYTES:
                return None
            f = tf.extractfile(member)
            if f is None:
                return None
            return _ACCEPTED.get(f.read(_MAX_REWARD_BYTES + 1))
    except (tarfile.TarError, EOFError, OSError, ValueError):
        return None


def build_command(task_dir: Path, tag: str) -> list[str]:
    return [
        "docker",
        "build",
        "-q",
        "-f",
        str(task_dir / "environment/Dockerfile"),
        "-t",
        tag,
        str(task_dir),
    ]


def create_command(image: str, name: str, solution_dir: Path | None, entry: str) -> list[str]:
    """`entry` is the grader path relative to the task dir, inside tests/.

    tests/ is not mounted: the host copies it in after the solution phase (`tests_copy_command`).
    No --rm: the stopped container must survive so the host can copy the reward out of it.
    """
    tests_entry = PurePosixPath(entry).relative_to("tests").as_posix()
    cmd = ["docker", "create", "--name", name, "--network", "none"]
    if solution_dir is not None:
        cmd += ["-v", f"{solution_dir}:/solution:ro"]
    cmd += ["-w", "/app", image, "bash", "-c", SCRIPT.format(entry=shlex.quote(tests_entry))]
    return cmd


def tests_copy_command(task_dir: Path, name: str) -> list[str]:
    """Copy tests/ into the stopped container as a writable /tests owned by root."""
    return ["docker", "cp", f"{task_dir / 'tests'}/.", f"{name}:/tests"]


def docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        done = subprocess.run(["docker", "version"], capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return done.returncode == 0


def _tail_text(text: str) -> str:
    return text.strip()[-DETAIL_TAIL_CHARS:]


_built: set[tuple[str, Path]] = set()


def _build(task_dir: Path, tag: str) -> str | None:
    """Build once per task. Returns an error detail, or None on success."""
    if (tag, task_dir) in _built:
        return None
    build = subprocess.run(
        build_command(task_dir, tag),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=BUILD_TIMEOUT_SECONDS,
    )
    if build.returncode != 0:
        return "docker build failed: " + _tail_text(build.stdout + build.stderr)
    _built.add((tag, task_dir))
    return None


def _run_container(cmd: list[str], name: str, timeout: int) -> tuple[int | None, str]:
    """Run to completion or kill at the timeout. Returns (exit code or None, stderr tail).

    The container's stdout is discarded and its stderr goes to a temp file, so a flooding
    solution cannot exhaust memory here.
    """
    with tempfile.TemporaryFile() as err:
        try:
            done = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=err, timeout=timeout)
            code: int | None = done.returncode
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", name], capture_output=True)
            code = None
        size = err.seek(0, 2)
        err.seek(max(0, size - DETAIL_TAIL_CHARS))
        return code, err.read().decode("utf-8", errors="replace")


def _read_reward(name: str) -> int | None:
    done = subprocess.run(
        ["docker", "cp", f"{name}:{REWARD_PATH}", "-"],
        capture_output=True,
        timeout=CP_TIMEOUT_SECONDS,
    )
    if done.returncode != 0:
        return None
    return parse_reward_tar(done.stdout)


def docker_runner(task_dir: Path, solution_dir: Path | None, timeout: int) -> RunResult:
    # docker treats a relative bind-mount source as a volume name, so mount absolute paths
    task_dir = task_dir.resolve()
    if solution_dir is not None:
        solution_dir = solution_dir.resolve()
    spec = load_task(task_dir)
    tag = f"kilmeh-selftest-{spec.id}"
    which = "none" if solution_dir is None else solution_dir.name
    name = f"{tag}-{which}-{time.time_ns()}"
    try:
        error = _build(task_dir, tag)
        if error:
            return RunResult(None, error)
        create = create_command(tag, name, solution_dir, spec.grader.entry)
        created = subprocess.run(create, capture_output=True, timeout=CP_TIMEOUT_SECONDS)
        if created.returncode != 0:
            return RunResult(None, "docker create failed: " + _tail_text(created.stderr.decode()))
        start = ["docker", "start", "-a", name]
        code, err_tail = _run_container(start, name, timeout)  # solution phase
        if code is None:
            return RunResult(None, f"timeout after {timeout}s (container killed)")
        planted = subprocess.run(
            ["docker", "cp", f"{name}:/tests", "-"], capture_output=True, timeout=CP_TIMEOUT_SECONDS
        )
        if planted.returncode == 0:
            return RunResult(None, "the solution created /tests (refused)")
        copied = subprocess.run(
            tests_copy_command(task_dir, name), capture_output=True, timeout=CP_TIMEOUT_SECONDS
        )
        if copied.returncode != 0:
            return RunResult(None, "copying tests/ failed: " + _tail_text(copied.stderr.decode()))
        code, err_tail = _run_container(start, name, timeout)  # grader phase
        if code is None:
            return RunResult(None, f"timeout after {timeout}s (container killed)")
        reward = _read_reward(name)
        if reward is None:
            return RunResult(
                None, f"no valid reward.txt (docker exit {code}): " + _tail_text(err_tail)
            )
        return RunResult(reward, "")
    except subprocess.TimeoutExpired:
        return RunResult(None, "docker timeout while building or reading the reward")
    except OSError as e:
        return RunResult(None, f"docker error: {e}")
    finally:
        try:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            pass


def selftest_task(task_dir: Path, runner: Runner = docker_runner) -> SelfTestResult:
    spec = load_task(task_dir)
    timeout = spec.grader.timeout_seconds
    return SelfTestResult(
        task_id=spec.id,
        reference=runner(task_dir, task_dir / spec.solutions.reference, timeout),
        known_bad=runner(task_dir, task_dir / spec.solutions.known_bad, timeout),
        untouched=runner(task_dir, None, timeout),
    )


def selftest_paths(paths: list[Path], runner: Runner = docker_runner) -> list[SelfTestResult]:
    return [selftest_task(t, runner) for t in find_task_dirs(paths)]
