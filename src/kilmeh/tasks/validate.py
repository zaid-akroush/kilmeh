"""Load and structurally validate task directories. Never runs Docker or solutions."""

import json
import re
import tomllib
from pathlib import Path, PurePosixPath

from pydantic import ValidationError

from kilmeh.tasks.models import TaskSpec

BOM = b"\xef\xbb\xbf"
REQUIRED_DIRS = ("fixture", "tests")
DOCKERFILE = "environment/Dockerfile"
SOLVE_ENTRY = "solve.sh"
VARIANT_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def load_task(task_dir: Path) -> TaskSpec:
    """Parse task.toml (UTF-8) into a TaskSpec.

    Raises OSError, UnicodeDecodeError, tomllib.TOMLDecodeError or ValidationError.
    """
    text = (task_dir / "task.toml").read_bytes().decode("utf-8")
    return TaskSpec.model_validate(tomllib.loads(text))


def find_task_dirs(paths: list[Path]) -> list[Path]:
    """A path is a task if it holds task.toml, otherwise search it recursively."""
    found: list[Path] = []
    for p in paths:
        if (p / "task.toml").is_file():
            found.append(p)
        else:
            found.extend(sorted(t.parent for t in p.rglob("task.toml")))
    return found


def _inside(root: Path, rel: str) -> Path | None:
    """Resolve a task-relative path (following symlinks).

    Returns None if it is absolute, uses '..', loops, or resolves outside the resolved task dir.
    """
    pp = PurePosixPath(rel)
    if pp.is_absolute() or ".." in pp.parts:
        return None
    try:
        path = (root / pp).resolve()
    except (RuntimeError, OSError):  # symlink loop, permission error
        return None
    return path if path.is_relative_to(root) else None


def _heldout_ok(root: Path) -> bool:
    """Heldout tasks must sit directly under the nearest `tasks/heldout/` (resolved path)."""
    parts = root.parts
    for i in range(len(parts) - 2, -1, -1):
        if parts[i] == "tasks":
            return parts[i + 1] == "heldout"
    return False


def _check_prompt_file(path: Path, label: str, errors: list[str]) -> None:
    data = path.read_bytes()
    if data.startswith(BOM):
        errors.append(f"{label}: starts with a UTF-8 BOM")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        errors.append(f"{label}: not valid UTF-8")
        return
    if not text.strip():
        errors.append(f"{label}: prompt file is empty or whitespace-only")
    if "\x00" in text:
        errors.append(f"{label}: prompt file contains a NUL character")


_COPY_RE = re.compile(r"^\s*(COPY|ADD|RUN)\s+(.*)$", re.IGNORECASE)


def _dockerfile_instructions(text: str) -> list[tuple[int, str]]:
    """Logical lines (backslash continuations joined) as (first line number, text)."""
    out: list[tuple[int, str]] = []
    current, start = "", 0
    for n, raw in enumerate(text.splitlines(), 1):
        if not current and (not raw.strip() or raw.lstrip().startswith("#")):
            continue
        if not current:
            start = n
        if raw.rstrip().endswith("\\"):
            current += raw.rstrip()[:-1] + " "
            continue
        out.append((start, current + raw))
        current = ""
    if current:
        out.append((start, current))
    return out


def _unquote(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return token[1:-1]
    return token


def _check_run_mounts(rest: str, where: str, errors: list[str]) -> None:
    """`RUN --mount` of the build context (bind without from=) would copy graders into the image."""
    for token in rest.split():
        if not token.startswith("--"):
            break  # flags come first; the command starts here
        if not token.lower().startswith("--mount="):
            continue
        value = _unquote(token.split("=", 1)[1])
        opts = {}
        for item in value.split(","):
            key, _, val = item.partition("=")
            opts[key.strip().lower()] = val.strip()
        if opts.get("type", "bind").lower() == "bind" and "from" not in opts:
            errors.append(
                f"{where}: RUN --mount of type bind needs from=<stage> (a bind mount of the "
                f"build context can reach files outside fixture/): {value}"
            )


def _check_dockerfile_sources(path: Path, label: str, errors: list[str]) -> None:
    """Every COPY/ADD source must be fixture or inside fixture/ (multi-stage copies are exempt)."""
    text = path.read_bytes().decode("utf-8", errors="replace")
    for lineno, line in _dockerfile_instructions(text):
        m = _COPY_RE.match(line)
        if not m:
            continue
        rest = m.group(2).strip()
        if m.group(1).upper() == "RUN":
            _check_run_mounts(rest, f"{label}: line {lineno}", errors)
            continue
        args: list = [_unquote(a) for a in rest.split()]
        if rest.startswith("["):
            try:
                args = json.loads(rest)
            except ValueError:
                pass
        flags = [a for a in args if isinstance(a, str) and a.startswith("--")]
        if any(f.lower().startswith("--from=") for f in flags):
            continue
        sources = [a for a in args if a not in flags][:-1]
        for src in sources:
            parts = PurePosixPath(str(src)).parts
            if not parts or parts[0] != "fixture" or ".." in parts:
                errors.append(
                    f"{label}: line {lineno}: {m.group(1).upper()} source must be fixture or "
                    f"inside fixture/: {src}"
                )


def validate_task_dir(task_dir: Path, strict: bool = False) -> list[str]:
    """Return a list of error strings for one task directory (empty means valid)."""
    toml_path = task_dir / "task.toml"
    root = task_dir.resolve()
    try:
        spec = load_task(task_dir)
    except (OSError, UnicodeDecodeError) as e:
        return [f"{toml_path}: cannot read as UTF-8 TOML: {e}"]
    except tomllib.TOMLDecodeError as e:
        return [f"{toml_path}: invalid TOML: {e}"]
    except ValidationError as e:
        return [
            f"{toml_path}: {'.'.join(str(x) for x in err['loc']) or '(root)'}: {err['msg']}"
            for err in e.errors()
        ]

    errors: list[str] = []
    if spec.id != root.name:
        errors.append(f"{toml_path}: id: '{spec.id}' must equal directory name '{root.name}'")
    if spec.split == "heldout" and not _heldout_ok(root):
        errors.append(
            f"{toml_path}: split: heldout tasks belong only under tasks/heldout/ (git-ignored)"
        )

    seen_files: dict[Path, str] = {}
    for name, prompt in spec.prompts.items():
        if not VARIANT_RE.fullmatch(name):
            errors.append(
                f"{toml_path}: prompts.{name!r}: variant name must match "
                f"{VARIANT_RE.pattern} (it becomes a folder name)"
            )
        label = f"{toml_path}: prompts.{name}.file"
        path = _inside(root, prompt.file)
        if path is None:
            errors.append(f"{label}: path must stay inside the task directory")
        elif not path.is_file():
            errors.append(f"{label}: file not found: {prompt.file}")
        else:
            if path in seen_files:
                errors.append(f"{label}: same file as prompts.{seen_files[path]}.file")
            seen_files[path] = name
            _check_prompt_file(path, label, errors)
        if strict and prompt.review_status == "draft":
            msg = (
                f"{toml_path}: prompts.{name}.review_status: 'draft' is not allowed in strict "
                "mode (needs native_authored or native_reviewed)"
            )
            if prompt.kind == "dialect" or prompt.script == "latin":
                msg += ". Dialect and Arabizi prompts are never machine-written alone."
            errors.append(msg)

    path = _inside(root, spec.grader.entry)
    if path is None or not path.is_file():
        errors.append(f"{toml_path}: grader.entry: not a file inside the task: {spec.grader.entry}")
    tests_dir = _inside(root, "tests")
    outside_tests = (
        path is not None
        and path.is_file()
        and (tests_dir is None or not path.is_relative_to(tests_dir))
    )
    if PurePosixPath(spec.grader.entry).parts[:1] != ("tests",) or outside_tests:
        errors.append(f"{toml_path}: grader.entry: must be inside tests/: {spec.grader.entry}")

    sol = spec.solutions
    resolved: dict[str, Path] = {}
    for field, rel in (("reference", sol.reference), ("known_bad", sol.known_bad)):
        path = _inside(root, rel)
        if path is None or not path.is_dir():
            errors.append(f"{toml_path}: solutions.{field}: directory not found: {rel}")
        elif path == root:
            errors.append(
                f"{toml_path}: solutions.{field}: must be a subdirectory, not the task root"
            )
        else:
            resolved[field] = path
            solve = _inside(root, f"{rel}/{SOLVE_ENTRY}")
            if solve is None or not solve.is_file():
                errors.append(f"{toml_path}: solutions.{field}: missing {SOLVE_ENTRY} in {rel}")
    if len(resolved) == 2:
        ref, bad = resolved["reference"], resolved["known_bad"]
        if ref == bad:
            errors.append(
                f"{toml_path}: solutions: reference and known_bad must be different paths"
            )
        elif ref.is_relative_to(bad) or bad.is_relative_to(ref):
            errors.append(f"{toml_path}: solutions: reference and known_bad must not be nested")

    for d in REQUIRED_DIRS:
        path = _inside(root, d)
        if path is None or not path.is_dir():
            errors.append(f"{task_dir}: missing required directory {d}/ (inside the task)")
    path = _inside(root, DOCKERFILE)
    if path is None or not path.is_file():
        errors.append(f"{task_dir}: missing required file {DOCKERFILE} (inside the task)")
    else:
        _check_dockerfile_sources(path, f"{task_dir}/{DOCKERFILE}", errors)
    return errors


def validate_paths(paths: list[Path], strict: bool = False) -> tuple[int, list[str]]:
    """Validate every task under paths. Returns (task_count, errors)."""
    errors = [f"{p}: path does not exist" for p in paths if not p.exists()]
    tasks = find_task_dirs([p for p in paths if p.exists()])
    for t in tasks:
        errors.extend(validate_task_dir(t, strict=strict))
    return len(tasks), errors
