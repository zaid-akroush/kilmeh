"""Track B worker: runs the agent's code and reports raw outputs. It decides nothing.

verify.py starts it with `python3 -I -S -c <this source> APP` (as uid 65534 when the grader is
root, which cannot read the locked /tests) in its own session. It reads the call list from
stdin, imports the agent's search module, and writes one JSON list of raw results to its
original stdout. The agent's prints go to stderr, which the parent discards. The stdlib is
imported first and the app directory is appended to the END of sys.path.

Search calls are the only ones that need identity facts, so the worker records them: for each
returned record, its id and the index of the input record it IS (same object and still equal
to a pristine copy), or -1; and a digest of the input list after the call, which the parent
compares with the digest of what it sent.
"""

import copy
import hashlib
import json
import os
import sys


def _run(call, mod):
    kind, args = call[0], call[1:]
    try:
        if kind == "norm":
            v = mod.normalize_for_search(args[0])
            return ["ok", v] if type(v) is str else ["badtype", type(v).__name__]
        if kind == "search":
            records, pristine = args[0], copy.deepcopy(args[0])
            found = mod.search(records, args[1])
            hits = []
            for r in found:
                idx = next((i for i, rec in enumerate(records) if r is rec), -1)
                if idx >= 0 and r != pristine[idx]:
                    idx = -1
                hits.append([r["id"], idx])
            # a digest, not a flag: the parent knows the digest of the records it sent
            digest = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
            return ["ok", hits, digest]
        if kind == "sort":
            names = list(args[0])
            v = mod.sort_names(names)
            if not (type(v) is list and all(type(x) is str for x in v)):
                return ["badtype", type(v).__name__]
            return ["ok", v]
        return ["err", "BadCall"]
    except BaseException as e:  # noqa: BLE001 - the agent may raise anything, even SystemExit
        return ["err", type(e).__name__]


def main() -> None:
    app = sys.argv[1]
    calls = json.load(sys.stdin)
    out = os.dup(1)
    os.dup2(2, 1)
    sys.path.append(app)
    try:
        import search as mod
    except BaseException:  # noqa: BLE001
        results = [["err", "ImportError"]] * len(calls)
    else:
        results = [_run(call, mod) for call in calls]
    data = json.dumps(results, ensure_ascii=True).encode("ascii")
    while data:
        data = data[os.write(out, data) :]


main()
