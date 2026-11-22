"""Write Harbor task folders (one per prompt variant) from Kilmeh tasks.

Files are copied as bytes: prompt and fixture text is never decoded here. Harbor is not a
dependency; this module only writes the folder layout and task.toml that Harbor reads.
"""

import json
import os
import shutil
from pathlib import Path

from kilmeh.tasks.models import TaskSpec
from kilmeh.tasks.validate import find_task_dirs, load_task, validate_paths

HARBOR_SCHEMA_VERSION = "1.4"
AGENT_TIMEOUT_SEC = 900
BUILD_TIMEOUT_SEC = 600
GRADER_ENTRY = "tests/test.sh"
_EXEC = 0o755
_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
PLACEHOLDER_PREFIX = b"TODO(board)"  # a prompt the board has not written yet; never exported


def _s(value: str) -> str:
    """A TOML basic string (JSON string escapes are valid TOML for these values)."""
    text = json.dumps(value, ensure_ascii=False)
    # json.dumps leaves DEL and C1 controls raw; TOML forbids them in basic strings
    return "".join(f"\\u{ord(c):04x}" if 0x7F <= ord(c) <= 0x9F else c for c in text)


def _task_toml(spec: TaskSpec, variant: str) -> str:
    prompt = spec.prompts[variant]
    keywords = ["kilmeh", spec.track, *spec.stack]
    meta = [
        ("kilmeh_task_id", spec.id),
        ("kilmeh_task_version", spec.version),
        ("track", spec.track),
        ("difficulty", spec.difficulty),
        ("split", spec.split),
        ("pair_id", spec.pair_id),
        ("variant", variant),
        ("lang", prompt.lang),
        ("kind", prompt.kind),
        ("script", prompt.script),
        ("dialect", prompt.dialect),
        ("review_status", prompt.review_status),
    ]
    lines = [
        f"schema_version = {_s(HARBOR_SCHEMA_VERSION)}",
        "",
        "[task]",
        f"name = {_s(f'kilmeh/{spec.id}--{variant}')}",
        f"description = {_s(spec.title)}",
        f"keywords = [{', '.join(_s(k) for k in keywords)}]",
        "",
        "[metadata]",
        *(f"{k} = {_s(v)}" for k, v in meta if v is not None),
        "",
        "[verifier]",
        f"timeout_sec = {spec.grader.timeout_seconds}",
        "",
        "[agent]",
        f"timeout_sec = {AGENT_TIMEOUT_SEC}",
        "",
        "[environment]",
        f"build_timeout_sec = {BUILD_TIMEOUT_SEC}",
        "",
    ]
    return "\n".join(lines)


def _check(task_dir: Path) -> TaskSpec:
    spec = load_task(task_dir)
    if spec.split == "heldout":
        raise ValueError(f"{task_dir}: held-out tasks are never exported")
    if spec.grader.entry != GRADER_ENTRY:
        raise ValueError(f"{task_dir}: grader.entry must be {GRADER_ENTRY} to export to Harbor")
    return spec


def _dest(spec: TaskSpec, variant: str, out_dir: Path) -> Path:
    """The variant folder path, or ValueError if it is unsafe to write."""
    dest = out_dir / f"{spec.id}--{variant}"
    if dest.is_symlink():
        raise ValueError(f"{dest}: is a symlink; remove it first")
    if dest.resolve().parent != out_dir.resolve() or dest.name != f"{spec.id}--{variant}":
        raise ValueError(f"{dest}: variant folder would be outside {out_dir}")
    if dest.exists() and not dest.is_dir():
        raise ValueError(f"{dest}: exists and is not a plain folder; remove it first")
    return dest


def _skipped(task_dir: Path, spec: TaskSpec, variant: str) -> bool:
    """A board placeholder, or a non-English prompt still in draft (AI-written or unreviewed,
    tasks/REVIEW_PROCESS.md): no native speaker has written it, so it is not exported."""
    prompt = spec.prompts[variant]
    if prompt.lang != "en" and prompt.review_status == "draft":
        return True
    return (task_dir / prompt.file).read_bytes().startswith(PLACEHOLDER_PREFIX)


def _export(task_dir: Path, spec: TaskSpec, out_dir: Path) -> list[Path]:
    created: list[Path] = []
    for variant in sorted(spec.prompts):
        if _skipped(task_dir, spec, variant):
            continue
        dest = _dest(spec, variant, out_dir)
        if dest.exists():
            shutil.rmtree(dest)
        (dest / "environment").mkdir(parents=True)
        shutil.copy2(task_dir / spec.prompts[variant].file, dest / "instruction.md")
        (dest / "task.toml").write_bytes(_task_toml(spec, variant).encode("utf-8"))
        shutil.copy2(task_dir / "environment/Dockerfile", dest / "environment/Dockerfile")
        shutil.copytree(task_dir / "fixture", dest / "environment/fixture", ignore=_IGNORE)
        shutil.copytree(task_dir / "tests", dest / "tests", ignore=_IGNORE)
        shutil.copytree(task_dir / spec.solutions.reference, dest / "solution", ignore=_IGNORE)
        for script in (dest / "solution/solve.sh", dest / GRADER_ENTRY):
            os.chmod(script, _EXEC)
        created.append(dest)
    return created


def export_task(task_dir: Path, out_dir: Path) -> list[Path]:
    """One Harbor folder per prompt variant, sorted by variant. Raises ValueError if refused."""
    spec = _check(task_dir)
    return _export(task_dir, spec, out_dir)


def export_paths(paths: list[Path], out_dir: Path) -> list[Path]:
    """Validate every task first; write nothing if any is invalid or refused."""
    _, errors = validate_paths(paths)
    if errors:
        raise ValueError("\n".join(errors))
    task_dirs = find_task_dirs(paths)
    specs = [_check(t) for t in task_dirs]
    for spec in specs:
        for variant in spec.prompts:
            _dest(spec, variant, out_dir)  # refuse before writing anything
    created: list[Path] = []
    try:
        for task_dir, spec in zip(task_dirs, specs, strict=True):
            created.extend(_export(task_dir, spec, out_dir))
    except OSError as e:
        raise ValueError(f"cannot write export: {e}") from e
    return created
