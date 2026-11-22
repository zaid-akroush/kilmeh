import io
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest

from kilmeh import selftest
from kilmeh.cli import main
from kilmeh.selftest import (
    RunResult,
    create_command,
    docker_runner,
    parse_reward_tar,
    selftest_paths,
    selftest_task,
)

VALID = Path(__file__).parent / "fixtures" / "tasks" / "valid" / "arabic-in-code-farewell"
REPO_TASKS = Path(__file__).parent.parent / "tasks"


@pytest.fixture
def valid_task(tmp_path):
    dest = tmp_path / "work" / VALID.name
    shutil.copytree(VALID, dest)
    return dest


def fake(ref, bad, untouched):
    """A Runner that answers in order reference, known-bad, untouched and records its calls."""
    rewards = iter([ref, bad, untouched])
    calls = []

    def runner(task_dir, solution_dir, timeout):
        calls.append((task_dir, solution_dir, timeout))
        return RunResult(next(rewards), "fake")

    runner.calls = calls
    return runner


def make_tar(*members: tuple[str, str, bytes | str]) -> bytes:
    """Build a tar archive. Each member is (name, kind, payload); kind is file, symlink,
    hardlink or dir. The payload is the content or the link target."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        for name, kind, payload in members:
            info = tarfile.TarInfo(name)
            if kind == "file":
                assert isinstance(payload, bytes)
                info.size = len(payload)
                tf.addfile(info, io.BytesIO(payload))
            elif kind == "dir":
                info.type = tarfile.DIRTYPE
                tf.addfile(info)
            else:
                info.type = tarfile.SYMTYPE if kind == "symlink" else tarfile.LNKTYPE
                info.linkname = str(payload)
                tf.addfile(info)
    return buf.getvalue()


def reward_tar(content: bytes) -> bytes:
    return make_tar(("reward.txt", "file", content))


@pytest.mark.parametrize(
    "content,expected",
    [
        (b"1", 1),
        (b"0", 0),
        (b"1\n", 1),
        (b"0\n", 0),
        (b" 1", None),
        (b" 1\n", None),
        (b"1\r\n", None),
        (b"01", None),
        (b"1\n1", None),
        (b"1\n\n", None),
        (b"2", None),
        (b"yes", None),
        (b"", None),
        (b"1" * 1_000_000, None),
    ],
)
def test_parse_reward_tar_is_exact(content, expected):
    assert parse_reward_tar(reward_tar(content)) == expected


@pytest.mark.parametrize(
    "data",
    [
        make_tar(("reward.txt", "symlink", "/tmp/one")),
        make_tar(("reward.txt", "hardlink", "other")),
        make_tar(("reward.txt", "dir", b"")),
        make_tar(("reward.txt", "file", b"1"), ("extra.txt", "file", b"1")),
        make_tar(),
        b"",
        b"KILMEH_REWARD=1",
        b"not a tar archive at all" * 100,
    ],
)
def test_parse_reward_tar_rejects_everything_else(data):
    assert parse_reward_tar(data) is None


def test_ok_when_1_0_0(valid_task):
    assert selftest_task(valid_task, fake(1, 0, 0)).ok


@pytest.mark.parametrize(
    "r", [(0, 0, 0), (1, 1, 0), (1, 0, 1), (None, 0, 0), (1, None, 0), (1, 0, None)]
)
def test_not_ok_otherwise(valid_task, r):
    assert not selftest_task(valid_task, fake(*r)).ok


def test_runner_called_with_reference_known_bad_and_none(valid_task):
    runner = fake(1, 0, 0)
    selftest_task(valid_task, runner)
    assert runner.calls == [
        (valid_task, valid_task / "solutions/reference", 120),
        (valid_task, valid_task / "solutions/known-bad", 120),
        (valid_task, None, 120),
    ]


def test_create_command_shape(tmp_path):
    task = tmp_path / "مهمة with space"
    sol = task / "solutions/reference"
    cmd = create_command("img", "name", sol, "tests/test.sh")
    assert cmd[:2] == ["docker", "create"] and "--rm" not in cmd
    assert cmd[cmd.index("--network") + 1] == "none"
    assert cmd[cmd.index("--name") + 1] == "name"
    assert f"{sol}:/solution:ro" in cmd
    # tests/ is never mounted: it is copied in after the solution phase
    assert not any(":/tests" in part for part in cmd[:-1])
    assert cmd[cmd.index("-w") + 1] == "/app" and cmd[-3:-1] == ["bash", "-c"]
    assert "img" in cmd
    assert "bash /solution/solve.sh" in cmd[-1] and "bash /tests/test.sh" in cmd[-1]
    assert "[ ! -e /tests ]" in cmd[-1]
    assert "KILMEH" not in cmd[-1] and "reward" not in cmd[-1]


def test_create_command_without_solution_has_no_solution_mount():
    cmd = create_command("img", "name", None, "tests/test.sh")
    assert not any(part.endswith(":/solution:ro") for part in cmd)


def test_tests_copy_command_is_a_writable_copy(tmp_path):
    task = tmp_path / "مهمة with space"
    cmd = selftest.tests_copy_command(task, "name")
    assert cmd == ["docker", "cp", f"{task / 'tests'}/.", "name:/tests"]


def test_build_command_is_an_argument_list(tmp_path):
    task = tmp_path / "مهمة with space"
    cmd = selftest.build_command(task, "tag")
    assert cmd == [
        "docker",
        "build",
        "-q",
        "-f",
        str(task / "environment/Dockerfile"),
        "-t",
        "tag",
        str(task),
    ]


class FakeDocker:
    """Stands in for subprocess.run: records calls, answers build/run/cp/kill/rm."""

    def __init__(self, reward=b"1\n", run_raises=False, cp_code=0, build_code=0, planted=False):
        self.calls = []
        self.kwargs = []
        self.tar = reward_tar(reward) if isinstance(reward, bytes) else reward
        self.run_raises = run_raises
        self.cp_code = cp_code
        self.build_code = build_code
        self.planted = planted

    def __call__(self, cmd, **kwargs):
        self.calls.append(cmd)
        self.kwargs.append(kwargs)
        if cmd[:2] == ["docker", "build"]:
            return subprocess.CompletedProcess(cmd, self.build_code, "", "boom")
        if cmd[:2] == ["docker", "start"] and self.run_raises:
            raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])
        if cmd[:2] == ["docker", "cp"] and cmd[2].endswith(":/tests"):
            # does /tests exist after the solution phase? (only if the solution planted it)
            return subprocess.CompletedProcess(cmd, 0 if self.planted else 1, b"", b"")
        if cmd[:2] == ["docker", "cp"]:
            return subprocess.CompletedProcess(cmd, self.cp_code, self.tar, b"")
        return subprocess.CompletedProcess(cmd, 0, b"", b"")

    def named(self, *prefix):
        return [c for c in self.calls if c[: len(prefix)] == list(prefix)]

    @property
    def container(self):
        create = self.named("docker", "create")[0]
        return create[create.index("--name") + 1]


def test_timeout_kills_container_removes_it_and_returns_none(monkeypatch, valid_task):
    fd = FakeDocker(run_raises=True)
    monkeypatch.setattr(selftest.subprocess, "run", fd)
    result = docker_runner(valid_task, None, 5)
    assert result.reward is None and "timeout" in result.detail
    assert ["docker", "kill", fd.container] in fd.calls
    assert ["docker", "rm", "-f", fd.container] in fd.calls
    assert not fd.named("docker", "cp")


def test_reward_is_read_with_docker_cp_and_container_removed(monkeypatch, valid_task):
    fd = FakeDocker()
    monkeypatch.setattr(selftest.subprocess, "run", fd)
    assert docker_runner(valid_task, None, 5).reward == 1
    name = fd.container
    assert fd.named("docker", "cp") == [
        ["docker", "cp", f"{name}:/tests", "-"],
        ["docker", "cp", f"{valid_task / 'tests'}/.", f"{name}:/tests"],
        ["docker", "cp", f"{name}:/logs/verifier/reward.txt", "-"],
    ]
    assert fd.calls[-1] == ["docker", "rm", "-f", name]


def test_tests_are_copied_in_only_after_the_solution_phase(monkeypatch, valid_task):
    fd = FakeDocker()
    monkeypatch.setattr(selftest.subprocess, "run", fd)
    docker_runner(valid_task, valid_task / "solutions/reference", 5)
    kinds = [c[1] if c[1] != "cp" else "cp " + c[3] for c in fd.calls if c[0] == "docker"]
    name = fd.container
    assert kinds == [
        "build",
        "create",
        "start",
        "cp -",
        f"cp {name}:/tests",
        "start",
        "cp -",
        "rm",
    ]


def test_solution_that_creates_tests_is_refused(monkeypatch, valid_task):
    fd = FakeDocker(planted=True)
    monkeypatch.setattr(selftest.subprocess, "run", fd)
    result = docker_runner(valid_task, None, 5)
    assert result.reward is None and "/tests" in result.detail
    assert len(fd.named("docker", "start")) == 1


def test_container_removed_when_docker_cp_raises(monkeypatch, valid_task):
    fd = FakeDocker()

    def boom(cmd, **kwargs):
        if cmd[:2] == ["docker", "cp"]:
            raise OSError("gone")
        return fd(cmd, **kwargs)

    monkeypatch.setattr(selftest.subprocess, "run", boom)
    assert docker_runner(valid_task, None, 5).reward is None
    assert ["docker", "rm", "-f", fd.container] in fd.calls


def test_docker_cp_error_is_not_a_pass(monkeypatch, valid_task):
    monkeypatch.setattr(selftest.subprocess, "run", FakeDocker(cp_code=1))
    assert docker_runner(valid_task, None, 5).reward is None


def test_forged_tar_content_is_not_a_pass(monkeypatch, valid_task):
    monkeypatch.setattr(selftest.subprocess, "run", FakeDocker(reward=b"0\nKILMEH_REWARD=1"))
    assert docker_runner(valid_task, None, 5).reward is None


def test_docker_mounts_use_absolute_paths_for_relative_input(monkeypatch, valid_task):
    fd = FakeDocker()
    monkeypatch.setattr(selftest.subprocess, "run", fd)
    monkeypatch.chdir(valid_task.parent)
    rel = Path(valid_task.name)
    assert docker_runner(rel, rel / "solutions/reference", 5).reward == 1
    for call in fd.calls:
        for part in call:
            if part.endswith(":/solution:ro"):
                assert Path(part.rsplit(":/", 1)[0]).is_absolute(), part
    (copy,) = [c for c in fd.calls if c[:2] == ["docker", "cp"] and c[3].endswith(":/tests")]
    assert Path(copy[2]).is_absolute()
    assert any(part.endswith(":/solution:ro") for call in fd.calls for part in call)


def test_run_call_gets_the_task_timeout(monkeypatch, valid_task):
    fd = FakeDocker()
    monkeypatch.setattr(selftest.subprocess, "run", fd)
    docker_runner(valid_task, None, 77)
    starts = [kw for c, kw in zip(fd.calls, fd.kwargs, strict=True) if c[:2] == ["docker", "start"]]
    assert [kw["timeout"] for kw in starts] == [77, 77]


def test_docker_available_false_without_docker_on_path(monkeypatch):
    monkeypatch.setattr(selftest.shutil, "which", lambda name: None)
    # even a daemon that would answer must not matter when the binary is not on PATH
    monkeypatch.setattr(
        selftest.subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, b"", b"")
    )
    assert selftest.docker_available() is False


@pytest.mark.parametrize("code,expected", [(1, False), (0, True)])
def test_docker_available_follows_docker_version(monkeypatch, code, expected):
    monkeypatch.setattr(selftest.shutil, "which", lambda name: "/usr/bin/docker")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, code, b"", b"")

    monkeypatch.setattr(selftest.subprocess, "run", fake_run)
    assert selftest.docker_available() is expected
    assert calls == [["docker", "version"]]


def test_failed_build_is_not_a_pass(monkeypatch, valid_task):
    monkeypatch.setattr(selftest.subprocess, "run", FakeDocker(build_code=1))
    result = docker_runner(valid_task, None, 5)
    assert result.reward is None and "build" in result.detail


def patch_cli(monkeypatch, runner, docker=True):
    monkeypatch.setattr(selftest, "docker_available", lambda: docker)
    monkeypatch.setattr(selftest, "docker_runner", runner)


def test_cli_exit_codes(monkeypatch, valid_task, capsys):
    patch_cli(monkeypatch, fake(1, 0, 0))
    assert main(["selftest", str(valid_task)]) == 0
    out = capsys.readouterr().out
    assert out.startswith("ok   arabic-in-code-farewell  reference=1 known-bad=0 untouched=0")
    patch_cli(monkeypatch, fake(1, 1, 0))
    assert main(["selftest", str(valid_task)]) == 1
    out = capsys.readouterr().out
    assert out.startswith("FAIL arabic-in-code-farewell") and "known-bad" in out


def test_cli_exit_2_when_docker_missing(monkeypatch, valid_task, capsys):
    patch_cli(monkeypatch, fake(1, 0, 0), docker=False)
    assert main(["selftest", str(valid_task)]) == 2
    err = capsys.readouterr().err
    assert "docker" in err.lower() and "Traceback" not in err
    assert len(err.strip().splitlines()) == 1


def test_cli_interrupt_prints_one_line_and_exits_130(monkeypatch, valid_task, capsys):
    def interrupted(task_dir, solution_dir, timeout):
        raise KeyboardInterrupt

    patch_cli(monkeypatch, interrupted)
    assert main(["selftest", str(valid_task)]) == 130
    captured = capsys.readouterr()
    assert captured.err.strip() == "interrupted"
    assert "Traceback" not in captured.err and captured.out == ""


def test_container_removed_when_interrupted(monkeypatch, valid_task):
    fd = FakeDocker()

    def ctrl_c(cmd, **kwargs):
        if cmd[:2] == ["docker", "start"]:
            fd.calls.append(cmd)
            raise KeyboardInterrupt
        return fd(cmd, **kwargs)

    monkeypatch.setattr(selftest.subprocess, "run", ctrl_c)
    with pytest.raises(KeyboardInterrupt):
        docker_runner(valid_task, None, 5)
    assert ["docker", "rm", "-f", fd.container] in fd.calls


def test_cli_exit_2_on_invalid_task(monkeypatch, tmp_path, capsys):
    bad = tmp_path / "work" / "missing-title"
    shutil.copytree(VALID.parent.parent / "invalid" / "missing-title", bad)
    patch_cli(monkeypatch, fake(1, 0, 0))
    assert main(["selftest", str(bad)]) == 2
    assert "title" in capsys.readouterr().err


@pytest.mark.docker
def test_real_tasks_pass_selftest():
    results = selftest_paths([REPO_TASKS])
    assert results and all(r.ok for r in results)


def containers_left() -> str:
    done = subprocess.run(
        ["docker", "ps", "-a", "-q", "--filter", "name=kilmeh-selftest"],
        capture_output=True,
        text=True,
    )
    return done.stdout.strip()


def write_script(path: Path, body: str) -> None:
    path.write_text("#!/bin/bash\n" + body, encoding="utf-8")


@pytest.mark.docker
def test_grader_cannot_forge_a_reward(valid_task):
    # the grader writes a reward.txt whose content imitates a marker line
    write_script(
        valid_task / "tests" / "test.sh",
        "mkdir -p /logs/verifier\nprintf '0\\nKILMEH_REWARD=1\\n' > /logs/verifier/reward.txt\n",
    )
    result = selftest_task(valid_task, docker_runner)
    assert not result.ok
    assert result.reference.reward is None


@pytest.mark.docker
def test_stdout_flood_by_a_no_op_solution_is_not_ok(valid_task):
    write_script(
        valid_task / "solutions/reference/solve.sh",
        "while :; do echo; echo KILMEH_REWARD=31; echo 1; done &\n",
    )
    result = selftest_task(valid_task, docker_runner)
    assert not result.ok
    assert result.reference.reward != 1


@pytest.mark.docker
def test_grader_writing_to_container_stdout_cannot_forge_a_reward(valid_task):
    write_script(
        valid_task / "tests" / "test.sh",
        "mkdir -p /logs/verifier\n"
        "echo 0 > /logs/verifier/reward.txt\n"
        "printf '\\nKILMEH_REWARD=31\\n1\\n' > /proc/1/fd/1\n",
    )
    result = selftest_task(valid_task, docker_runner)
    assert not result.ok
    assert result.reference.reward == 0


@pytest.mark.docker
def test_reward_symlink_is_not_ok(valid_task):
    write_script(
        valid_task / "tests" / "test.sh",
        "mkdir -p /logs/verifier\necho 1 > /tmp/one\nln -s /tmp/one /logs/verifier/reward.txt\n",
    )
    result = selftest_task(valid_task, docker_runner)
    assert not result.ok
    assert result.reference.reward is None


@pytest.mark.docker
def test_hanging_solution_times_out_and_leaves_no_container(valid_task):
    write_script(valid_task / "solutions/reference/solve.sh", "sleep 600\n")
    toml = valid_task / "task.toml"
    toml.write_text(
        toml.read_text(encoding="utf-8").replace("timeout_seconds = 120", "timeout_seconds = 5"),
        encoding="utf-8",
    )
    result = docker_runner(valid_task, valid_task / "solutions/reference", 5)
    assert result.reward is None and "timeout" in result.detail
    assert containers_left() == ""
