# Harbor verifier body. Runs in the container with the python3 stdlib only.
# Prints the JSON report to stdout and one `PASS key: detail` / `FAIL key: detail` line per
# check to stderr. The details are fixed text: no input or expected value is printed.
import ast
import json
import os
import random
import sys
import types

APP = os.environ.get("KILMEH_APP", "/app")
TARGET = "paging.py"
FUNC = "get_page"
HERE = os.path.dirname(os.path.abspath(__file__))

DETAIL = {
    "file_exists": "paging.py exists",
    "no_bom": "file has no byte order mark",
    "utf8": "file is valid UTF-8",
    "imports": "file imports without error",
    "same_function_set": "no public function added or removed",
    "name_and_signature": "get_page keeps its name and arguments",
    "first_page": "page 1 gives the first items",
    "middle_pages": "pages in the middle give the right items",
    "last_partial_page": "the last, shorter page gives the rest",
    "past_end_empty": "a page past the end (or an empty list) gives an empty list",
    "input_not_mutated": "the input list is left unchanged",
}


def rb(p):
    with open(p, "rb") as f:
        return f.read()


def funcs(tree):
    return {
        n.name: n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def public(names):
    return {n for n in names if not n.startswith("_")}


def expect(items, page, per_page):
    return items[(page - 1) * per_page : page * per_page]


def cases():
    rng = random.SystemRandom()
    out = {k: [] for k in ("first", "middle", "last", "past")}
    for _ in range(25):
        per = rng.randint(2, 6)
        n = rng.randint(per * 3 + 1, per * 5 - 1)  # at least 3 full pages, last page partial
        if n % per == 0:
            n += 1
        items = [rng.randint(0, 999) for _ in range(n)]
        pages = -(-n // per)
        out["first"].append((items, 1, per))
        out["middle"].append((items, rng.randint(2, pages - 1), per))
        out["last"].append((items, pages, per))
        out["past"].append((items, pages + rng.randint(1, 3), per))
    out["first"] += [(list(range(10)), 1, 3), (list(range(10)), 1, 10)]
    out["middle"] += [(list(range(10)), 2, 3), (list(range(10)), 3, 3)]
    out["last"] += [(list(range(10)), 4, 3), (list(range(5)), 1, 10)]
    out["past"] += [([], 1, 3), (list(range(10)), 5, 3), (list(range(10)), 2, 10)]
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
        data.decode("utf-8")
        res["utf8"] = True
    except UnicodeDecodeError:
        res["utf8"] = False
    # Later checks run on a lenient decode (BOM dropped, bad bytes replaced) so each
    # file-level problem fails only its own check.
    src = data.decode("utf-8", errors="replace").lstrip("\ufeff")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        res["imports"] = False
        return res

    orig = ast.parse(rb(os.path.join(HERE, "golden", "orig.py")).decode("utf-8"))
    ofuncs, nfuncs = funcs(orig), funcs(tree)
    res["same_function_set"] = public(ofuncs) == public(nfuncs)
    fn = nfuncs.get(FUNC)
    res["name_and_signature"] = fn is not None and ast.dump(fn.args) == ast.dump(ofuncs[FUNC].args)

    try:
        m = types.ModuleType("paging_mod")
        m.__file__ = path
        exec(compile(src, path, "exec"), m.__dict__)
        res["imports"] = True
        f = getattr(m, FUNC)
    except Exception:  # noqa: BLE001
        res["imports"] = False
        return res
    groups = {
        "first_page": "first",
        "middle_pages": "middle",
        "last_partial_page": "last",
        "past_end_empty": "past",
    }
    cs = cases()
    for key, g in groups.items():
        try:
            res[key] = all(f(list(i), p, n) == expect(i, p, n) for i, p, n in cs[g])
        except Exception:  # noqa: BLE001
            res[key] = False
    try:
        probe = [5, 3, 4, 1, 2]
        f(probe, 2, 2)
        res["input_not_mutated"] = probe == [5, 3, 4, 1, 2]
    except Exception:  # noqa: BLE001
        res["input_not_mutated"] = False
    return res


raw = check()
res = {k: raw.get(k, False) for k in DETAIL}
print(json.dumps(res, indent=1))
for k, ok in res.items():
    print(
        f"{'PASS' if ok else 'FAIL'} {k}: {DETAIL[k] if ok else 'expected ' + DETAIL[k]}",
        file=sys.stderr,
    )
sys.exit(0 if all(res.values()) else 1)
