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
TARGET = "invoice.py"
HERE = os.path.dirname(os.path.abspath(__file__))
CALLERS = ("invoice_total", "receipt_line")

DETAIL = {
    "file_exists": "invoice.py exists",
    "no_bom": "file has no byte order mark",
    "utf8": "file is valid UTF-8",
    "imports": "file imports without error",
    "helper_defined": "add_tax exists and takes one argument",
    "only_helper_added": "no public function added or removed besides add_tax",
    "signatures_unchanged": "invoice_total and receipt_line keep their arguments",
    "helper_behaviour": "add_tax adds the tax and rounds to 2 decimals",
    "invoice_total_unchanged": "invoice_total gives the same results as before",
    "receipt_line_unchanged": "receipt_line gives the same text as before",
    "invoice_total_uses_helper": "invoice_total calls add_tax",
    "receipt_line_uses_helper": "receipt_line calls add_tax",
    "rate_not_repeated": "the tax rate is not written again in invoice_total or receipt_line",
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


def old_total(prices):
    s = 0
    for p in prices:
        s += p
    return round(s * 1.16, 2)


def old_line(name, price):
    return f"{name}: {round(price * 1.16, 2):.2f}"


def has_rate(fn):
    return any(
        isinstance(n, ast.Constant) and n.value in (1.16, 0.16, 16, 116) for n in ast.walk(fn)
    )


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
    helper = nfuncs.get("add_tax")
    if helper is not None:
        a = helper.args
        res["helper_defined"] = (
            len(a.posonlyargs + a.args) == 1
            and not a.kwonlyargs
            and a.vararg is None
            and a.kwarg is None
        )
    res["only_helper_added"] = public(nfuncs) == public(ofuncs) | {"add_tax"}
    res["signatures_unchanged"] = all(
        c in nfuncs and ast.dump(nfuncs[c].args) == ast.dump(ofuncs[c].args) for c in CALLERS
    )
    res["rate_not_repeated"] = all(c in nfuncs and not has_rate(nfuncs[c]) for c in CALLERS)

    try:
        m = types.ModuleType("invoice_mod")
        m.__file__ = path
        exec(compile(src, path, "exec"), m.__dict__)
        res["imports"] = True
    except Exception:  # noqa: BLE001
        res["imports"] = False
        return res

    rng = random.SystemRandom()
    lists = [[], [100], [0.1, 0.2, 0.3], [19.99, 5.01]] + [
        [round(rng.uniform(0, 500), 2) for _ in range(rng.randint(1, 6))] for _ in range(8)
    ]
    prices = [0, 100, 9.99, 0.05] + [round(rng.uniform(0, 900), 2) for _ in range(8)]
    try:
        res["helper_behaviour"] = all(m.add_tax(p) == round(p * 1.16, 2) for p in prices)
    except Exception:  # noqa: BLE001
        res["helper_behaviour"] = False
    try:
        res["invoice_total_unchanged"] = all(
            m.invoice_total(list(p)) == old_total(p) for p in lists
        )
    except Exception:  # noqa: BLE001
        res["invoice_total_unchanged"] = False
    try:
        res["receipt_line_unchanged"] = all(
            m.receipt_line("Tea", p) == old_line("Tea", p) for p in prices
        )
    except Exception:  # noqa: BLE001
        res["receipt_line_unchanged"] = False

    # Swap the helper for a stub: a caller that really goes through add_tax shows the stub's result.
    try:
        m.add_tax = lambda amount: amount + 1000
        res["invoice_total_uses_helper"] = m.invoice_total([10, 20]) == 1030
        res["receipt_line_uses_helper"] = m.receipt_line("Tea", 5) == "Tea: 1005.00"
    except Exception:  # noqa: BLE001
        res.setdefault("invoice_total_uses_helper", False)
        res.setdefault("receipt_line_uses_helper", False)
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
