"""Task 001 worker: imports the agent's module and reports raw outputs. It decides nothing.

verify.py starts it with `python3 -I -c <this source> APP` (as uid 65534 when the grader is
root) in its own session. It reads the names to try from stdin, imports the app, and writes one
JSON list of [farewell(name), greet(name)] per name to its original stdout; the agent's prints
go to stderr, which the parent discards. The app directory is appended to the END of sys.path
(after the stdlib), so تحية.py may import its own helper modules. The agent's code runs in this
process and can forge anything written here; the parent stays safe because the names are drawn
at random per run.
"""

import importlib.util
import json
import os
import sys


def _call(fn, name):
    try:
        v = fn(name)
    except BaseException as e:  # noqa: BLE001 - the agent may raise anything, even SystemExit
        return ["err", type(e).__name__]
    return ["ok", v] if isinstance(v, str) else ["ok", None]


def main() -> None:
    app = sys.argv[1]
    names = json.load(sys.stdin)
    out = os.dup(1)
    os.dup2(2, 1)
    sys.path.append(app)
    try:
        spec = importlib.util.spec_from_file_location("tahiyya", os.path.join(app, "تحية.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        results = [[_call(m.farewell, n), _call(m.greet, n)] for n in names]
    except BaseException as e:  # noqa: BLE001
        results = [["err", type(e).__name__]]
    data = json.dumps(results).encode("ascii")
    while data:
        data = data[os.write(out, data) :]


main()
