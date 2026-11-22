# Harbor verifier body. Runs in the container with the python3 stdlib only.
# Prints the JSON report to stdout and one `PASS key: detail` / `FAIL key: detail` line per
# check to stderr. The details are fixed text: no input or expected value is printed.
import ast
import json
import os
import random
import string
import sys
import types

APP = os.environ.get("KILMEH_APP", "/app")
TARGET = "price.py"
HERE = os.path.dirname(os.path.abspath(__file__))

DETAIL = {
    "file_exists": "price.py exists",
    "no_bom": "file has no byte order mark",
    "utf8": "file is valid UTF-8",
    "imports": "file imports without error",
    "same_function_set": "no public function added or removed",
    "format_price_signature": "format_price takes amount, then an optional currency",
    "line_text_signature": "line_text keeps its name and arguments",
    "default_unchanged": "calls without currency give the same text as before",
    "custom_currency": "a given currency (positional or by name) is used",
    "line_text_works": "line_text still works and still uses the default currency",
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
    fp = nfuncs.get("format_price")
    if fp is not None:
        a = fp.args
        pos = [x.arg for x in a.posonlyargs + a.args]
        kwonly = {k.arg: d for k, d in zip(a.kwonlyargs, a.kw_defaults, strict=True)}
        res["format_price_signature"] = (
            a.vararg is None
            and a.kwarg is None
            and (
                (pos == ["amount", "currency"] and len(a.defaults) == 1 and not kwonly)
                or (
                    pos == ["amount"]
                    and set(kwonly) == {"currency"}
                    and kwonly["currency"] is not None
                )
            )
        )
    lt = nfuncs.get("line_text")
    res["line_text_signature"] = lt is not None and ast.dump(lt.args) == ast.dump(
        ofuncs["line_text"].args
    )

    try:
        m = types.ModuleType("price_mod")
        m.__file__ = path
        exec(compile(src, path, "exec"), m.__dict__)
        res["imports"] = True
    except Exception:  # noqa: BLE001
        res["imports"] = False
        return res

    rng = random.SystemRandom()
    amounts = [0, 5, 2.5, 1234.567] + [round(rng.uniform(0, 5000), 3) for _ in range(6)]
    codes = ["USD", "EUR", "SAR"] + [
        "".join(rng.choice(string.ascii_uppercase) for _ in range(3)) for _ in range(3)
    ]
    try:
        res["default_unchanged"] = all(m.format_price(a) == f"{a:.2f} JOD" for a in amounts)
    except Exception:  # noqa: BLE001
        res["default_unchanged"] = False
    try:
        res["custom_currency"] = all(
            m.format_price(a, currency=c) == f"{a:.2f} {c}" for a in amounts for c in codes
        )
    except Exception:  # noqa: BLE001
        res["custom_currency"] = False
    try:
        res["line_text_works"] = all(m.line_text("Tea", a) == f"Tea: {a:.2f} JOD" for a in amounts)
    except Exception:  # noqa: BLE001
        res["line_text_works"] = False
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
