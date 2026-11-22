import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

TASK = Path(__file__).parent.parent / "tasks" / "a-prompts" / "loop-for-to-while"
LOOP_PROMPTS = TASK / "prompts"

# Board-authored prompts (native Jordanian speaker). Deliberate edits must update these
# hashes in the same PR.
BOARD_PROMPT_SHA256 = {
    "en.md": "cadc05e394945ba18746987c02925d54bb3b20b7a48424b567341dc0a63cf87f",
    "arabizi_levantine.md": "56b86e680d27ce0e85b93ae4ee5b0cf826d91e2edfb50f9b56cd8e489cff34ab",
    "levantine.md": "60c716ec63dc2944a8a7a1b5a04ee17c96db597de8b335c7d13c9bc10dafaf18",
}


def test_board_authored_prompts_are_byte_exact():
    for name, expected in BOARD_PROMPT_SHA256.items():
        data = (LOOP_PROMPTS / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected, name


def test_board_authored_prompts_end_with_single_newline_no_bom():
    for name in BOARD_PROMPT_SHA256:
        data = (LOOP_PROMPTS / name).read_bytes()
        assert data.endswith(b"\n") and not data.endswith(b"\n\n"), name
        assert not data.startswith(b"\xef\xbb\xbf"), name


def test_golden_orig_is_byte_identical_to_fixture():
    assert (TASK / "tests" / "golden" / "orig.py").read_bytes() == (
        TASK / "fixture" / "numbers.py"
    ).read_bytes()


HEAD = "def sum_positive(numbers):\n"
DECOY = "    i = 0\n    while i < 1:\n        i += 1\n"

# name -> (source, expected reward)
SOURCES = {
    # legitimate alternatives: must score 1
    "alt_while_index": (
        HEAD
        + "    total = 0\n    i = 0\n    while i < len(numbers):\n"
        + "        if numbers[i] > 0:\n            total += numbers[i]\n        i += 1\n"
        + "    return total\n",
        1,
    ),
    "alt_while_pop0": (
        HEAD
        + "    items = list(numbers)\n    total = 0\n    while items:\n"
        + "        n = items.pop(0)\n        if n > 0:\n            total += n\n"
        + "    return total\n",
        1,
    ),
    "alt_while_iter_next": (
        HEAD
        + "    it = iter(numbers)\n    total = 0\n    while True:\n"
        + "        try:\n            n = next(it)\n        except StopIteration:\n"
        + "            break\n"
        + "        if n > 0:\n            total += n\n    return total\n",
        1,
    ),
    "alt_while_try_indexerror": (
        HEAD
        + "    total = 0\n    i = 0\n    while True:\n        try:\n"
        + "            n = numbers[i]\n        except IndexError:\n            break\n"
        + "        if n > 0:\n            total += n\n        i += 1\n    return total\n",
        1,
    ),
    # rewrites that must score 0
    "sum_map_decoy": (
        HEAD + DECOY + "    return sum(map(lambda n: n if n > 0 else 0, numbers))\n",
        0,
    ),
    "sum_filter_decoy": (
        HEAD + DECOY + "    return sum(filter(lambda n: n > 0, numbers))\n",
        0,
    ),
    "reduce_decoy": (
        "from functools import reduce\n\n\n"
        + HEAD
        + DECOY
        + "    return reduce(lambda a, n: a + (n if n > 0 else 0), numbers, 0)\n",
        0,
    ),
    "itertools_compress_decoy": (
        "import itertools\n\n\n"
        + HEAD
        + DECOY
        + "    return sum(itertools.compress(numbers, [n > 0 for n in numbers]))\n",
        0,
    ),
    "itertools_from_import_decoy": (
        "from itertools import accumulate as acc\n\n\n"
        + HEAD
        + DECOY
        + "    acc([])\n    total = 0\n    i = 0\n    while i < len(numbers):\n"
        + "        if numbers[i] > 0:\n            total += numbers[i]\n        i += 1\n"
        + "    return total\n",
        0,
    ),
    "dead_if_false_while": (
        HEAD
        + "    if False:\n        i = 0\n        while i < 1:\n            i += 1\n"
        + "    return sum(map(lambda n: max(n, 0), numbers))\n",
        0,
    ),
    "dead_while_false": (
        HEAD
        + "    total = 0\n    while False:\n        total += 1\n"
        + "    return sum([n for n in numbers if n > 0])\n",
        0,
    ),
    "import_inside_function": (
        HEAD
        + "    import itertools\n"
        + DECOY
        + "    return sum(itertools.islice([n for n in numbers if n > 0], None))\n",
        0,
    ),
    "globals_recursion": (
        HEAD
        + DECOY
        + "    if not numbers:\n        return 0\n    f = globals()['sum_positive']\n"
        + "    return f(numbers[1:]) + max(numbers[0], 0)\n",
        0,
    ),
    "while_wrong_result": (
        HEAD
        + "    total = 0\n    i = 0\n    while i < len(numbers):\n"
        + "        if numbers[i] > 0:\n            total += numbers[i]\n        i += 2\n"
        + "    return total\n",
        0,
    ),
    "for_loop_unchanged": ((TASK / "fixture" / "numbers.py").read_text(), 0),
}


def grade(tmp_path, source, fresh=True):
    app = tmp_path / "app"
    if fresh:
        app.mkdir()
    data = source if isinstance(source, bytes) else source.encode("utf-8")
    (app / "numbers.py").write_bytes(data)
    env = dict(os.environ, KILMEH_APP=str(app))
    proc = subprocess.run(
        [sys.executable, "-I", str(TASK / "tests" / "verify.py")],
        env=env,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout


def run_solution(tmp_path, solve_py):
    app = tmp_path / "app"
    app.mkdir()
    (app / "numbers.py").write_bytes((TASK / "fixture" / "numbers.py").read_bytes())
    subprocess.run([sys.executable, "-I", str(solve_py), str(app / "numbers.py")], check=True)
    return grade(tmp_path, (app / "numbers.py").read_text(encoding="utf-8"), fresh=False)


def test_reference_solution_passes_grader_exit_code_0(tmp_path):
    assert run_solution(tmp_path, TASK / "solutions" / "reference" / "solve.py")[0] == 0


def test_known_bad_solution_fails_grader_exit_code_1(tmp_path):
    assert run_solution(tmp_path, TASK / "solutions" / "known-bad" / "solve.py")[0] == 1


@pytest.mark.parametrize("name", sorted(SOURCES))
def test_grader_ast_logic(tmp_path, name):
    source, want = SOURCES[name]
    code, out = grade(tmp_path, source)
    assert code == (0 if want == 1 else 1), f"{name}\n{out}"


# ---------------------------------------------------------------------------------------
# Isolated checks: each source makes EXACTLY the listed verify.py keys False.
# ---------------------------------------------------------------------------------------

LOOP = (
    "    total = 0\n    i = 0\n    while i < len(numbers):\n"
    "        if numbers[i] > 0:\n            total += numbers[i]\n        i += 1\n"
    "    return total\n"
)


def build(extra="", pre="", head=HEAD, loop=LOOP, post=""):
    """A correct while-index solution with `extra` statements at the top of the body."""
    return pre + head + extra + loop + post


def verdict(tmp_path, source):
    code, out = grade(tmp_path, source)
    data = json.loads(out[out.index("{\n") :])
    assert code == (0 if all(data.values()) else 1)
    return {k for k, v in data.items() if not v}


ZERO_BRANCH = "    if len(numbers) < 0:\n"

ISOLATED = {}


def isolated(name, source, failing):
    ISOLATED[name] = (source, set(failing))


# legit sources: nothing may fail
isolated("legit_base", build(), [])
isolated("legit_unused_module_import", build(pre="import itertools\n\n\n"), [])
isolated(
    "legit_if_not_false_wraps_live_while",
    build(extra="    if not False:\n        j = 0\n        while j < 0:\n            j += 1\n"),
    [],
)
isolated(
    "legit_if_true_with_live_while",
    build(extra="    if True:\n        j = 0\n        while j < 0:\n            j += 1\n"),
    [],
)

# no_forbidden_calls: one forbidden name each (module-level `name = None` keeps it runnable
# and keeps the name out of the itertools/functools import scan)
for _name in [
    "sum", "map", "filter", "reduce", "any", "all",
    "globals", "locals", "eval", "exec", "__import__", "itertools", "functools",
]:  # fmt: skip
    isolated(
        f"forbidden_name_{_name}",
        build(extra=f"    _ = {_name}\n", pre=f"{_name} = None\n\n\n"),
        ["no_forbidden_calls"],
    )
# names bound by importing from itertools/functools (module level), incl. aliases
for _label, _pre, _use in [
    ("from_itertools", "from itertools import accumulate", "accumulate"),
    ("from_itertools_alias", "from itertools import accumulate as acc", "acc"),
    ("import_itertools_alias", "import itertools as it", "it"),
    ("from_functools", "from functools import partial", "partial"),
    ("from_functools_alias", "from functools import partial as part", "part"),
    ("import_functools_alias", "import functools as ft", "ft"),
]:
    isolated(
        f"module_import_{_label}",
        build(extra=f"    _ = {_use}\n", pre=_pre + "\n\n\n"),
        ["no_forbidden_calls"],
    )
# imports inside the function
isolated("import_inside_function", build(extra="    import os\n"), ["no_forbidden_calls"])
isolated(
    "from_import_inside_function", build(extra="    from os import path\n"), ["no_forbidden_calls"]
)

# while_reachable: dead whiles (each shape on its own)
for _label, _extra in [
    ("while_false", "    while False:\n        pass\n"),
    ("while_zero", "    while 0:\n        pass\n"),
    ("if_false", "    if False:\n        while True:\n            break\n"),
    ("if_zero", "    if 0:\n        while True:\n            break\n"),
    ("if_not_true", "    if not True:\n        while True:\n            break\n"),
    (
        "else_of_if_true",
        "    if True:\n        pass\n    else:\n        while True:\n            break\n",
    ),
]:  # fmt: skip
    isolated(f"dead_{_label}", build(extra=_extra), ["while_reachable"])

# has_while: no while at all (while_reachable needs a live while, behaviour is wrong too)
isolated("no_while", HEAD + "    return 0\n", ["has_while", "while_reachable", "behaviour"])

# no_recursion, no_comprehension (each type), no_for (sync and async)
isolated(
    "recursion",
    build(extra=ZERO_BRANCH + "        sum_positive([])\n"),
    ["no_recursion"],
)
for _label, _expr in [
    ("listcomp", "[x for x in numbers]"),
    ("setcomp", "{x for x in numbers}"),
    ("dictcomp", "{x: x for x in numbers}"),
    ("genexp", "(x for x in numbers)"),
]:
    isolated(
        f"comprehension_{_label}",
        build(extra=ZERO_BRANCH + f"        _ = {_expr}\n"),
        ["no_comprehension"],
    )
isolated(
    "for_loop",
    build(extra=ZERO_BRANCH + "        for _x in numbers:\n            pass\n"),
    ["no_for"],
)
# a nested async def is the only place an async for can live; it also adds a function
isolated(
    "async_for",
    build(extra="    async def _inner():\n        async for _x in numbers:\n            pass\n"),
    ["no_for", "same_function_set"],
)

# signature, function set, mutation of input, behaviour
isolated(
    "renamed_parameter",
    build(head="def sum_positive(items):\n", loop=LOOP.replace("numbers", "items")),
    ["name_and_signature"],
)
isolated(
    "extra_parameter",
    build(head="def sum_positive(numbers, extra=0):\n"),
    ["name_and_signature"],
)
isolated(
    "extra_function",
    build(post="\n\ndef helper():\n    return 1\n"),
    ["same_function_set"],
)
isolated(
    "input_mutated",
    HEAD
    + "    total = 0\n    while numbers:\n        n = numbers.pop(0)\n"
    + "        if n > 0:\n            total += n\n    return total\n",
    ["input_not_mutated"],
)
isolated("wrong_behaviour", build(loop=LOOP.replace("> 0", "> 1")), ["behaviour"])

# file-level checks
isolated("syntax_error", b"def sum_positive(numbers:\n", ["imports"])
isolated("invalid_utf8", b"def sum_positive(numbers):\n    return \xff\n", ["utf8"])
isolated("module_raises_on_import", build(pre="raise RuntimeError('boom')\n\n\n"), [
    "imports", "behaviour", "input_not_mutated",
])  # fmt: skip
# ast.parse of the decoded text rejects a leading U+FEFF, so `imports` fails with it
isolated("bom", b"\xef\xbb\xbf" + build().encode("utf-8"), ["no_bom", "imports"])


@pytest.mark.parametrize("name", sorted(ISOLATED))
def test_each_check_fails_in_isolation(tmp_path, name):
    source, failing = ISOLATED[name]
    assert verdict(tmp_path, source) == failing, name


def test_verify_app_default_is_container_path():
    tree = ast.parse((TASK / "tests" / "verify.py").read_text(encoding="utf-8"))
    (assign,) = [
        n
        for n in tree.body
        if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "APP" for t in n.targets)
    ]
    call = assign.value
    assert isinstance(call, ast.Call) and call.args[0].value == "KILMEH_APP"
    assert call.args[1].value == "/app"
