# Harbor verifier body. Runs in the container with the python3 stdlib only.
import ast
import importlib.util
import json
import os
import sys

APP = os.environ.get("KILMEH_APP", "/app")
TARGET = "numbers.py"
FUNC = "sum_positive"
HERE = os.path.dirname(os.path.abspath(__file__))

CASES = [
    ([], 0),
    ([5], 5),
    ([-5], 0),
    ([0], 0),
    ([1, 2, 3], 6),
    ([-1, -2, -3], 0),
    ([3, -1, 4, -1, 5], 12),
    ([0, 0, 7], 7),
    ([10, -10, 10], 20),
]


def rb(p):
    with open(p, "rb") as f:
        return f.read()


def funcs(tree):
    return {n.name: n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def sig(fn):
    return ast.dump(fn.args)


FORBIDDEN_NAMES = {
    "sum", "map", "filter", "reduce", "any", "all",
    "globals", "locals", "eval", "exec", "__import__", "itertools", "functools",
}  # fmt: skip


def _const_truth(test):
    """True/False for a constant test, None if not a simple constant."""
    if isinstance(test, ast.Constant):
        return bool(test.value)
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        inner = _const_truth(test.operand)
        return None if inner is None else not inner
    return None


def scan_whiles(stmts):
    """Return (live_whiles, dead_whiles), skipping code under constant-false branches."""
    live, dead = 0, 0

    def visit(node):
        nonlocal live, dead
        if isinstance(node, ast.While):
            if _const_truth(node.test) is False:
                dead += 1
                return  # body is unreachable too, but count it as dead
            live += 1
        if isinstance(node, ast.If):
            truth = _const_truth(node.test)
            if truth is False:
                dead += sum(isinstance(n, ast.While) for b in node.body for n in ast.walk(b))
            else:
                for b in node.body:
                    visit(b)
            if truth is True:
                dead += sum(isinstance(n, ast.While) for b in node.orelse for n in ast.walk(b))
            else:
                for b in node.orelse:
                    visit(b)
            return
        for child in ast.iter_child_nodes(node):
            visit(child)

    for stmt in stmts:
        visit(stmt)
    return live, dead


def banned_names(tree):
    """Names bound at module level from itertools/functools (e.g. `from itertools import x`)."""
    out = set()
    for n in tree.body:
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.split(".")[0] in ("itertools", "functools"):
                    out.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] in (
            "itertools",
            "functools",
        ):
            for a in n.names:
                out.add(a.asname or a.name)
    return out


def check():
    res = {}
    path = os.path.join(APP, TARGET)
    try:
        data = rb(path)
    except OSError:
        return {"file_exists": False}
    res["file_exists"] = True
    res["no_bom"] = not data.startswith(b"\xef\xbb\xbf")
    try:
        src = data.decode("utf-8")
    except UnicodeDecodeError:
        res["utf8"] = False
        return res
    res["utf8"] = True
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        print("syntax error:", e)
        res["imports"] = False
        return res

    orig = ast.parse(rb(os.path.join(HERE, "golden", "orig.py")).decode("utf-8"))
    ofuncs, nfuncs = funcs(orig), funcs(tree)
    res["same_function_set"] = set(ofuncs) == set(nfuncs)
    fn = nfuncs.get(FUNC)
    res["name_and_signature"] = fn is not None and sig(fn) == sig(ofuncs[FUNC])

    if fn is not None:
        body = [n for stmt in fn.body for n in ast.walk(stmt)]
        res["has_while"] = any(isinstance(n, ast.While) for n in body)
        res["no_for"] = not any(isinstance(n, (ast.For, ast.AsyncFor)) for n in body)
        res["no_comprehension"] = not any(
            isinstance(n, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)) for n in body
        )
        banned = FORBIDDEN_NAMES | banned_names(tree)
        res["no_forbidden_calls"] = not any(
            (isinstance(n, ast.Name) and n.id in banned)
            or isinstance(n, (ast.Import, ast.ImportFrom))
            for n in body
        )
        live, dead = scan_whiles(fn.body)
        res["while_reachable"] = live > 0 and dead == 0
        res["no_recursion"] = not any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == FUNC
            for n in body
        )
    else:
        for k in (
            "has_while",
            "no_for",
            "no_comprehension",
            "no_recursion",
            "no_forbidden_calls",
            "while_reachable",
        ):
            res[k] = False

    try:
        spec = importlib.util.spec_from_file_location("numbers_mod", path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        res["imports"] = True
        f = getattr(m, FUNC)
        res["behaviour"] = all(f(list(inp)) == want for inp, want in CASES)
        probe = [1, -2, 3]
        f(probe)
        res["input_not_mutated"] = probe == [1, -2, 3]
    except Exception as e:  # noqa: BLE001
        print("import/run error:", e)
        res.setdefault("imports", False)
        res.setdefault("behaviour", False)
        res.setdefault("input_not_mutated", False)
    return res


res = check()
print(json.dumps(res, indent=1))
sys.exit(0 if res and all(res.values()) else 1)
