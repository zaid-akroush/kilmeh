"""Command line entry point: `kilmeh validate-tasks`, `selftest`, `summarize-run` etc."""

import argparse
import sys
from pathlib import Path

from kilmeh import harbor, results_page, selftest, summarize
from kilmeh.arabizi_key import validate_arabizi
from kilmeh.tasks.validate import validate_paths


def _reward(run: selftest.RunResult) -> str:
    return "none" if run.reward is None else str(run.reward)


def _format(r: selftest.SelfTestResult) -> str:
    runs = (
        ("reference", r.reference, 1),
        ("known-bad", r.known_bad, 0),
        ("untouched", r.untouched, 0),
    )
    summary = " ".join(f"{name}={_reward(run)}" for name, run, _ in runs)
    if r.ok:
        return f"ok   {r.task_id}  {summary}"
    lines = [f"FAIL {r.task_id}  {summary}"]
    for name, run, want in runs:
        if run.reward != want:
            lines.append(f"     {name}: got {_reward(run)}, expected {want}. {run.detail}".rstrip())
    return "\n".join(lines)


def _selftest(paths: list[Path]) -> int:
    count, errors = validate_paths(paths)
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    if errors:
        print(f"FAILED: {len(errors)} error(s) in {count} task(s)", file=sys.stderr)
        return 2
    if count == 0:
        print("error: no tasks found", file=sys.stderr)
        return 2
    if not selftest.docker_available():
        print(
            "error: docker is not available (is it installed and is the daemon running?)",
            file=sys.stderr,
        )
        return 2
    results = selftest.selftest_paths(paths, runner=selftest.docker_runner)
    for r in results:
        print(_format(r))
    return 0 if all(r.ok for r in results) else 1


def _export_harbor(out_dir: Path, paths: list[Path]) -> int:
    try:
        created = harbor.export_paths(paths, out_dir)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for folder in created:
        print(folder)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kilmeh")
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate-tasks", help="structurally validate task directories")
    v.add_argument("paths", nargs="*", type=Path, default=[Path("tasks")])
    v.add_argument(
        "--strict",
        action="store_true",
        help="release checks (rejects every prompt still marked draft)",
    )
    t = sub.add_parser(
        "selftest", help="prove in Docker that each task's reference passes and known-bad fails"
    )
    t.add_argument("paths", nargs="*", type=Path, default=[Path("tasks")])
    h = sub.add_parser("export-harbor", help="write Harbor task folders, one per prompt variant")
    h.add_argument("out_dir", type=Path)
    h.add_argument("paths", nargs="*", type=Path, default=[Path("tasks")])
    a = sub.add_parser("validate-arabizi", help="validate the Arabizi answer key")
    a.add_argument("path", nargs="?", type=Path, default=Path("data/arabizi"))
    s = sub.add_parser("summarize-run", help="markdown pass rates from a Harbor jobs dir")
    s.add_argument("jobs_dir", type=Path)
    s.add_argument("--tasks", type=Path, default=Path("tasks"), help="tasks dir, for tracks")
    s.add_argument("--jsonl", type=Path, help="also write one JSON record per trial here")
    r = sub.add_parser("results-page", help="one self-contained HTML results page")
    r.add_argument("out_html", type=Path)
    r.add_argument("jobs_dirs", nargs="+", type=Path)
    r.add_argument("--tasks", type=Path, default=Path("tasks"), help="tasks dir, for tracks")
    r.add_argument("--title", default="Kilmeh results")
    args = parser.parse_args(argv)

    if args.command == "results-page":
        leaks = [x for d in args.jobs_dirs for x in summarize.find_leaks(d)]
        for leak in leaks:
            print(f"error: token-like string in {leak}", file=sys.stderr)
        if leaks:
            print("aborted: nothing written; remove the secrets first", file=sys.stderr)
            return 2
        try:
            page = results_page.render(args.jobs_dirs, args.tasks, args.title)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        args.out_html.write_text(page, encoding="utf-8", newline="\n")
        print(f"wrote {args.out_html}")
        return 0

    if args.command == "summarize-run":
        leaks = summarize.find_leaks(args.jobs_dir)
        for leak in leaks:
            print(f"error: token-like string in {leak}", file=sys.stderr)
        if leaks:
            print("aborted: nothing printed; remove the secrets first", file=sys.stderr)
            return 2
        try:
            table = summarize.summarize(args.jobs_dir, args.tasks)
            if args.jsonl:
                summarize.write_jsonl(args.jobs_dir, args.jsonl)
            if hasattr(sys.stdout, "reconfigure"):  # Windows redirect defaults to cp1252
                sys.stdout.reconfigure(encoding="utf-8")
            print(table)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        return 0

    if args.command == "validate-arabizi":
        pairs, errs = validate_arabizi(args.path)
        for e in errs:
            print(f"error: {e}", file=sys.stderr)
        if errs:
            print(f"FAILED: {len(errs)} error(s) in {pairs} pair(s)", file=sys.stderr)
            return 1
        print(f"OK: {pairs} pair(s) valid")
        return 0

    if args.command == "selftest":
        try:
            return _selftest(args.paths)
        except KeyboardInterrupt:
            print("interrupted", file=sys.stderr)
            return 130

    if args.command == "export-harbor":
        return _export_harbor(args.out_dir, args.paths)

    count, errors = validate_paths(args.paths, strict=args.strict)
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    if errors:
        print(f"FAILED: {len(errors)} error(s) in {count} task(s)", file=sys.stderr)
        return 1
    print(f"OK: {count} task(s) valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
