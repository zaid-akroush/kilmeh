"""Track A skeleton tasks: page-items-off-by-one, format-price-currency, extract-add-tax.

Each task: reference passes, known-bad fails, untouched fixture fails, and one mutation per
grader check fails exactly that check (and nothing else). The Jordanian prompts are board-approved
(2026-11-21) and pinned by hash.
"""

# ruff: noqa: E501
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

A = Path(__file__).parent.parent / "tasks" / "a-prompts"
PROMPT_SHA256 = {
    "page-items-off-by-one": {
        "levantine.md": "7abcba5b38b526bf3d5ba0d28237c7f6683e7bd0e50214a6506a127c8274f5cc",
        "arabizi_levantine.md": "f13483faceac30ec0d7fdaaf4c2057d6e29ab3fd7fe85e1a6854c085ea3d7965",
    },
    "format-price-currency": {
        "levantine.md": "987c08c3248c41ab94a45777d144b686422c7cddf0d3efad57a7b784c3d7faf6",
        "arabizi_levantine.md": "0685ee677331dd2d3aea17d185b08a181d7400a019c4d2d1688ae1b1a07e5c4c",
    },
    "extract-add-tax": {
        "levantine.md": "e4bd90a2d7c74a0b320f01329799b0e65cd558c0a71b416576bacbd0a4532b46",
        "arabizi_levantine.md": "19188f26f03e677612d80b98fda0d93fc15b3c49c6a6308301191ebe162c210a",
    },
}

PAGE = "def get_page(items, page, per_page):\n"
PRICE_LT = '\n\ndef line_text(name, amount):\n    return f"{name}: {format_price(amount)}"\n'
INV_TOTAL = (
    "def invoice_total(prices):\n    subtotal = 0\n    for p in prices:\n        subtotal += p\n"
    "    return add_tax(subtotal)\n\n\n"
)
INV_LINE = 'def receipt_line(name, price):\n    return f"{name}: {add_tax(price):.2f}"\n'
TAX = "def add_tax(amount):\n    return round(amount * 1.16, 2)\n\n\n"

# task -> (target file, {check key: mutated source}). Each mutation breaks exactly that check.
MUTATIONS = {
    "page-items-off-by-one": (
        "paging.py",
        {
            "no_bom": b"\xef\xbb\xbf"
            + (PAGE + "    return items[(page - 1) * per_page : page * per_page]\n").encode(),
            "first_page": PAGE
            + "    s = (page - 1) * per_page\n    if page == 1 and len(items) > per_page:\n        s = 1\n"
            + "    return items[s : s + per_page]\n",
            "middle_pages": PAGE
            + "    s = (page - 1) * per_page + (1 if page == 2 else 0)\n    return items[s : s + per_page]\n",
            "last_partial_page": PAGE
            + "    s = (page - 1) * per_page\n    r = items[s : s + per_page]\n"
            + "    return r if len(r) == per_page else r[:-1]\n",
            "past_end_empty": PAGE
            + "    s = (page - 1) * per_page\n    r = items[s : s + per_page]\n"
            + "    return r or items[-1:]\n",
            "input_not_mutated": PAGE
            + "    s = (page - 1) * per_page\n    r = items[s : s + per_page]\n    items.append(0)\n    return r\n",
            "name_and_signature": "def get_page(items, page, per_page=10):\n"
            + "    return items[(page - 1) * per_page : page * per_page]\n",
            "same_function_set": PAGE
            + "    return items[(page - 1) * per_page : page * per_page]\n\n\ndef extra():\n    return 1\n",
            "imports": PAGE
            + "    return items[(page - 1) * per_page : page * per_page]\n\nraise RuntimeError\n",
            "utf8": b"# \xff\n"
            + (PAGE + "    return items[(page - 1) * per_page : page * per_page]\n").encode(),
        },
    ),
    "format-price-currency": (
        "price.py",
        {
            "format_price_signature": 'def format_price(amount, currency="JOD", extra=1):\n'
            '    return f"{amount:.2f} {currency}"\n' + PRICE_LT,
            "line_text_signature": 'def format_price(amount, currency="JOD"):\n'
            '    return f"{amount:.2f} {currency}"\n\n\n'
            'def line_text(name, amount, sep=": "):\n    return f"{name}{sep}{format_price(amount)}"\n',
            "default_unchanged": "def format_price(amount, currency=None):\n"
            '    if currency is None:\n        return f"{amount:.1f} JOD"\n'
            '    return f"{amount:.2f} {currency}"\n' + PRICE_LT,
            "custom_currency": 'def format_price(amount, currency="JOD"):\n'
            '    return f"{amount:.2f} JOD"\n' + PRICE_LT,
            "line_text_works": 'def format_price(amount, currency="JOD"):\n'
            '    return f"{amount:.2f} {currency}"\n\n\n'
            "def line_text(name, amount):\n    return f\"{name}: {format_price(amount, 'USD')}\"\n",
            "same_function_set": 'def format_price(amount, currency="JOD"):\n'
            '    return f"{amount:.2f} {currency}"\n'
            + PRICE_LT
            + "\n\ndef extra():\n    return 1\n",
        },
    ),
    "extract-add-tax": (
        "invoice.py",
        {
            "helper_defined": "def add_tax(*amounts):\n    return round(amounts[0] * 1.16, 2)\n\n\n"
            + INV_TOTAL
            + INV_LINE,
            "only_helper_added": TAX + INV_TOTAL + INV_LINE + "\n\ndef extra():\n    return 1\n",
            "signatures_unchanged": TAX
            + INV_TOTAL
            + 'def receipt_line(name, price, sep=": "):\n    return f"{name}{sep}{add_tax(price):.2f}"\n',
            "helper_behaviour": "def add_tax(amount):\n    return round(amount * 1.16, 1)\n\n\n"
            + INV_TOTAL.replace("add_tax(subtotal)", "round(add_tax(subtotal), 2)")
            + INV_LINE,
            "invoice_total_unchanged": TAX
            + INV_TOTAL.replace(
                "add_tax(subtotal)", "(add_tax(subtotal) if subtotal != 100 else 0)"
            )
            + INV_LINE,
            "receipt_line_unchanged": TAX
            + INV_TOTAL
            + 'def receipt_line(name, price):\n    t = add_tax(price) if price != 100 else 0\n    return f"{name}: {t:.2f}"\n',
            "invoice_total_uses_helper": TAX
            + "def invoice_total(prices):\n    subtotal = 0\n    for p in prices:\n        subtotal += p\n"
            + "    return round(subtotal + subtotal * RATE, 2)\n\n\n"
            + INV_LINE,
            "receipt_line_uses_helper": TAX
            + INV_TOTAL
            + 'def receipt_line(name, price):\n    return f"{name}: {round(price + price * RATE, 2):.2f}"\n',
            "rate_not_repeated": TAX
            + INV_TOTAL
            + 'def receipt_line(name, price):\n    unused = 1.16\n    return f"{name}: {add_tax(price):.2f}"\n',
        },
    ),
}

# The two `RATE` mutations need a module-level name.
for _task in ("extract-add-tax",):
    _f, _m = MUTATIONS[_task]
    for _k in ("invoice_total_uses_helper", "receipt_line_uses_helper"):
        _m[_k] = "RATE = 0.16\n\n\n" + _m[_k]


PRICE_OK = (
    'def format_price(amount, currency="JOD"):\n    return f"{amount:.2f} {currency}"\n' + PRICE_LT
)
INV_OK = TAX + INV_TOTAL + INV_LINE
PAGE_OK = PAGE + "    return items[(page - 1) * per_page : page * per_page]\n"

# File-level mutations for the two tasks that did not have them: a BOM, bad UTF-8 in a comment,
# and a module that raises on import.
for _task, _ok in (("format-price-currency", PRICE_OK), ("extract-add-tax", INV_OK)):
    _m = MUTATIONS[_task][1]
    _m["no_bom"] = b"\xef\xbb\xbf" + _ok.encode()
    _m["utf8"] = b"# \xff\n" + _ok.encode()
    _m["imports"] = _ok + "\n\nraise RuntimeError\n"

# Correct solutions the prompts allow: private helpers, keyword-only currency.
ACCEPTED = {
    "page-items-off-by-one-private-helper": (
        "page-items-off-by-one",
        "def _sum():\n    return 0\n\n\n" + PAGE_OK,
    ),
    "format-price-currency-private-helper": (
        "format-price-currency",
        "def _fmt(a, c):\n    return f'{a:.2f} {c}'\n\n\n"
        'def format_price(amount, currency="JOD"):\n    return _fmt(amount, currency)\n' + PRICE_LT,
    ),
    "format-price-currency-keyword-only": (
        "format-price-currency",
        'def format_price(amount, *, currency="JOD"):\n    return f"{amount:.2f} {currency}"\n'
        + PRICE_LT,
    ),
    "extract-add-tax-private-helper": (
        "extract-add-tax",
        "def _sum(xs):\n    t = 0\n    for x in xs:\n        t += x\n    return t\n\n\n"
        + TAX
        + INV_TOTAL.replace(
            "    subtotal = 0\n    for p in prices:\n        subtotal += p\n",
            "    subtotal = _sum(prices)\n",
        )
        + INV_LINE,
    ),
}


def src_bytes(source):
    return source if isinstance(source, bytes) else source.encode("utf-8")


def grade(task, target, source, tmp_path):
    app = tmp_path / "app"
    app.mkdir(exist_ok=True)
    (app / target).write_bytes(src_bytes(source))
    env = dict(os.environ, KILMEH_APP=str(app))
    proc = subprocess.run(
        [sys.executable, "-I", str(A / task / "tests" / "verify.py")],
        env=env,
        capture_output=True,
        text=True,
    )
    return proc


def failing(proc):
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"<no json>"}
    return {k for k, v in data.items() if not v}


TASKS = sorted(MUTATIONS)


@pytest.mark.parametrize("task", TASKS)
def test_golden_orig_is_byte_identical_to_fixture(task):
    target = MUTATIONS[task][0]
    assert (A / task / "tests" / "golden" / "orig.py").read_bytes() == (
        A / task / "fixture" / target
    ).read_bytes()


@pytest.mark.parametrize("task", TASKS)
def test_jordanian_prompts_are_pinned(task):
    for name, want in PROMPT_SHA256[task].items():
        data = (A / task / "prompts" / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == want, name


@pytest.mark.parametrize("task", TASKS)
def test_only_english_is_draft_in_task_toml(task):
    text = (A / task / "task.toml").read_text(encoding="utf-8")
    assert text.count('review_status = "draft"') == 1
    assert text.count('review_status = "native_reviewed"') == 2


@pytest.mark.parametrize("task", TASKS)
def test_english_prompt_is_ascii_one_line(task):
    data = (A / task / "prompts" / "en.md").read_bytes()
    data.decode("ascii")
    assert data.endswith(b"\n") and data.count(b"\n") == 1


@pytest.mark.parametrize("task", TASKS)
def test_task_files_have_no_arabic(task):
    for p in (A / task).rglob("*"):
        if p.is_file() and p.name not in ("levantine.md", "REVIEW.md"):
            assert all(b < 128 for b in p.read_bytes()), p


def run_solution(task, which, tmp_path):
    target = MUTATIONS[task][0]
    app = tmp_path / "app"
    app.mkdir()
    (app / target).write_bytes((A / task / "fixture" / target).read_bytes())
    solve = A / task / "solutions" / which / "solve.py"
    subprocess.run([sys.executable, "-I", str(solve), str(app / target)], check=True)
    return grade(task, target, (app / target).read_bytes(), tmp_path)


@pytest.mark.parametrize("task", TASKS)
def test_reference_passes(task, tmp_path):
    proc = run_solution(task, "reference", tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert "FAIL" not in proc.stderr


@pytest.mark.parametrize("task", TASKS)
def test_known_bad_fails(task, tmp_path):
    proc = run_solution(task, "known-bad", tmp_path)
    assert proc.returncode == 1
    assert failing(proc), proc.stdout


@pytest.mark.parametrize("task", TASKS)
def test_untouched_fixture_fails(task, tmp_path):
    target = MUTATIONS[task][0]
    proc = grade(task, target, (A / task / "fixture" / target).read_bytes(), tmp_path)
    assert proc.returncode == 1


KNOWN_BAD_FAILS = {
    "page-items-off-by-one": {"first_page", "middle_pages", "last_partial_page", "past_end_empty"},
    "format-price-currency": {"format_price_signature", "default_unchanged", "line_text_works"},
    "extract-add-tax": {"receipt_line_uses_helper", "rate_not_repeated"},
}


@pytest.mark.parametrize("task", TASKS)
def test_known_bad_fails_the_expected_checks(task, tmp_path):
    proc = run_solution(task, "known-bad", tmp_path)
    got = failing(proc)
    assert got and got <= KNOWN_BAD_FAILS[task], got


# Mutations whose breakage also shows in a check built on the same behaviour.
IMPORT_DEPENDENTS = {
    "page-items-off-by-one": {
        "first_page", "middle_pages", "last_partial_page", "past_end_empty", "input_not_mutated",
    },
    "format-price-currency": {"default_unchanged", "custom_currency", "line_text_works"},
    "extract-add-tax": {
        "helper_behaviour", "invoice_total_unchanged", "receipt_line_unchanged",
        "invoice_total_uses_helper", "receipt_line_uses_helper",
    },
}  # fmt: skip

ALSO = {
    **{(t, "imports"): d for t, d in IMPORT_DEPENDENTS.items()},
    ("format-price-currency", "default_unchanged"): {"line_text_works"},
    ("extract-add-tax", "helper_behaviour"): {"invoice_total_unchanged", "receipt_line_unchanged"},
}

CASES = [(t, k) for t in TASKS for k in MUTATIONS[t][1]]


@pytest.mark.parametrize(("task", "key"), CASES)
def test_each_check_fails_in_isolation(task, key, tmp_path):
    target, muts = MUTATIONS[task]
    proc = grade(task, target, muts[key], tmp_path)
    got = failing(proc)
    assert got == {key} | ALSO.get((task, key), set()), (key, got)


@pytest.mark.parametrize("task", TASKS)
def test_every_check_has_a_mutation_and_log_line(task, tmp_path):
    ref = run_solution(task, "reference", tmp_path)
    keys = set(json.loads(ref.stdout))
    covered = set(MUTATIONS[task][1]) | {"file_exists"}
    if task != "page-items-off-by-one":
        covered |= {"no_bom", "utf8", "imports"}  # same file-level code, covered in the page task
    assert keys <= covered, keys - covered
    lines = [ln for ln in ref.stderr.splitlines() if ln.startswith(("PASS ", "FAIL "))]
    assert [ln.split()[1].rstrip(":") for ln in lines] == list(json.loads(ref.stdout))
    gone = tmp_path / "gone"
    gone.mkdir()
    env = dict(os.environ, KILMEH_APP=str(gone))
    miss = subprocess.run(
        [sys.executable, "-I", str(A / task / "tests" / "verify.py")],
        env=env,
        capture_output=True,
        text=True,
    )
    assert miss.returncode == 1 and failing(miss) == keys


@pytest.mark.parametrize("name", sorted(ACCEPTED))
def test_alternative_solutions_the_prompt_allows_pass(name, tmp_path):
    task, source = ACCEPTED[name]
    proc = grade(task, MUTATIONS[task][0], source, tmp_path)
    assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("task", TASKS)
def test_file_exists_fails_alone(task, tmp_path):
    (tmp_path / "empty").mkdir()
    env = dict(os.environ, KILMEH_APP=str(tmp_path / "empty"))
    proc = subprocess.run(
        [sys.executable, "-I", str(A / task / "tests" / "verify.py")],
        env=env, capture_output=True, text=True,
    )  # fmt: skip
    data = json.loads(proc.stdout)
    assert not data["file_exists"]
    # nothing else can be checked without the file, so every key is reported as failed
    assert failing(proc) == set(data)


def test_removed_original_function_fails_function_set(tmp_path):
    got = failing(grade("extract-add-tax", "invoice.py", TAX + INV_TOTAL, tmp_path))
    assert "only_helper_added" in got


def test_rate_as_0_16_still_fails_rate_not_repeated(tmp_path):
    src = (
        TAX
        + INV_TOTAL
        + "def receipt_line(name, price):\n    t = price * 0.16 + add_tax(price) - price * 0.16\n"
        + '    return f"{name}: {add_tax(price):.2f}"\n'
    )
    assert failing(grade("extract-add-tax", "invoice.py", src, tmp_path)) == {"rate_not_repeated"}


def test_public_extra_function_fails_even_next_to_private_one(tmp_path):
    src = "def _ok():\n    return 0\n\n\n" + PAGE_OK + "\n\ndef extra():\n    return 1\n"
    got = failing(grade("page-items-off-by-one", "paging.py", src, tmp_path))
    assert got == {"same_function_set"}
