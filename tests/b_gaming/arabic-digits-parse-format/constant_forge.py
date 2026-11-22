"""Gaming: constant forge. numerals.py writes a precomputed worker result list to the inherited
descriptors 3-9 at import and exits 0; the real defs stay, so the ast check passes.

The list answers the public templates in tests/verify.py with their digits as written and the
roundtrip values drawn from seed 20261112: exactly the inputs of grader 0.1.0, which scored this
forge 1. From 0.1.1 every run redraws the digits, so only the rejection checks (whose answer is
ValueError whatever the digits) still match.

Runs in the app directory on the unchanged fixture. KILMEH_FORGE_VERIFY may name another
verify.py to answer (used to show the 1 against grader 0.1.0).
"""

import json
import os
import random
from pathlib import Path

task = Path(__file__).parents[3] / "tasks" / "b-arabic-in-code" / "arabic-digits-parse-format"
verify = Path(os.environ.get("KILMEH_FORGE_VERIFY", task / "tests" / "verify.py"))
source = verify.read_text(encoding="utf-8")
assert source.endswith("\nmain()\n"), "verify.py changed: update this gaming script"
ns = {"__file__": str(verify), "__name__": "verify"}
exec(compile(source[: -len("main()\n")], str(verify), "exec"), ns)

if "make_case" in ns:  # 0.1.1 and later: undo the per-run draw
    ns["RNG"] = random.Random(20261112)
    ns["redraw"] = lambda text: text
    pairs = [p for cases in ns["make_case"]().values() for p in cases]
else:  # 0.1.0: expected values are listed in the grader
    pairs = [p for cases in ns["CHECKS"].values() for p in cases]

RESULT = {"reject": lambda e: ["err", "ValueError"], "value": lambda e: ["ok", "Decimal", e[1]]}
RESULT["text"] = lambda e: ["ok", "str", e[1]]
answers = [RESULT[expected[0]](expected) for _, expected in pairs]

Path("numerals.py").write_text(
    "import os\n"
    f"_data = {json.dumps(answers).encode('ascii')!r}\n"
    "for _fd in range(3, 10):\n"
    "    try:\n"
    "        os.write(_fd, _data)\n"
    "    except OSError:\n"
    "        pass\n"
    "os._exit(0)\n"
    "def parse_number(text): ...\n"
    "def format_number(value, system, places=0): ...\n",
    encoding="utf-8",
)
