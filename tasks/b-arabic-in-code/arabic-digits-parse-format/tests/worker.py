"""Track B worker: runs the agent's code and reports raw outputs. It decides nothing.

verify.py starts it with `python3 -I -S -c <this source> APP` (as uid 65534 when the grader is
root, which cannot read the locked /tests) in its own session. It reads the
call list from stdin, imports the agent's modules, and writes one JSON list of raw results to
its original stdout. The agent's prints go to stderr, which the parent discards. The stdlib is
imported first and the app directory is appended to the END of sys.path, so a planted
/app/json.py cannot shadow it. Whatever this process prints, the parent compares the outputs
with expected values it holds itself.
"""

import json
import os
import sys
from decimal import Decimal


def _value(v):
    return Decimal(v) if isinstance(v, str) else int(v)


def _decimal_result(v):
    return ["ok", "Decimal", str(v)] if type(v) is Decimal else ["ok", type(v).__name__, ""]


def _str_result(v):
    return ["ok", "str", v] if type(v) is str else ["ok", type(v).__name__, ""]


def _run(call, numerals, invoice):
    kind, args = call[0], call[1:]
    try:
        if kind == "parse":
            return _decimal_result(numerals.parse_number(args[0]))
        if kind == "format":
            value, rest = _value(args[0]), args[1:]
            return _str_result(numerals.format_number(value, *rest))
        if kind == "roundtrip":
            text = numerals.format_number(_value(args[0]), args[1], args[2])
            return _decimal_result(numerals.parse_number(text))
        if kind == "total":
            return _str_result(invoice.total_text(list(args[0]), args[1]))
        return ["err", "BadCall"]
    except BaseException as e:  # noqa: BLE001 - the agent may raise anything, even SystemExit
        return ["err", "ValueError" if isinstance(e, ValueError) else type(e).__name__]


def main() -> None:
    app = sys.argv[1]
    calls = json.load(sys.stdin)
    out = os.dup(1)
    os.dup2(2, 1)
    sys.path.append(app)
    try:
        import invoice
        import numerals
    except BaseException:  # noqa: BLE001
        results = [["err", "ImportError"]] * len(calls)
    else:
        results = [_run(call, numerals, invoice) for call in calls]
    data = json.dumps(results, ensure_ascii=True).encode("ascii")
    while data:
        data = data[os.write(out, data) :]


main()
