"""Structural checks for the static contribute-words site (site/contribute/).

No browser needed. The JS unit tests run through `node --test` when Node is on PATH.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site" / "contribute"
SCHEMA = SITE / "supabase" / "schema.sql"
AR_PLACEHOLDER = "TODO: board Arabic"
CATEGORIES = {"ui-label", "programming", "everyday-app", "greeting-polite", "tech-kept-english"}
DIALECTS = ["levantine", "gulf", "egyptian", "maghrebi", "iraqi", "sudanese", "other"]
# Agreed mapping, in display order (alphabetical by English country name).
COUNTRY_DIALECT = {
    "DZ": "maghrebi",
    "BH": "gulf",
    "KM": "other",
    "DJ": "other",
    "EG": "egyptian",
    "IQ": "iraqi",
    "JO": "levantine",
    "KW": "gulf",
    "LB": "levantine",
    "LY": "maghrebi",
    "MR": "maghrebi",
    "MA": "maghrebi",
    "OM": "gulf",
    "PS": "levantine",
    "QA": "gulf",
    "SA": "gulf",
    "SO": "other",
    "SD": "sudanese",
    "SY": "levantine",
    "TN": "maghrebi",
    "AE": "gulf",
    "YE": "other",
}
_ARABIC_BLOCKS = (
    (0x0600, 0x06FF),
    (0x0750, 0x077F),
    (0x08A0, 0x08FF),
    (0xFB50, 0xFDFF),
    (0xFE70, 0xFEFF),
)
ARABIC_RANGES = re.compile("[" + "".join(f"{chr(a)}-{chr(b)}" for a, b in _ARABIC_BLOCKS) + "]")
ISSUES_URL = "https://github.com/kilmeh/contribute/issues"
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
SUPABASE_REF = "hbkhgfupsibyjfngedmi"  # public by design
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _placeholders(value: str) -> list[str]:
    return sorted(re.findall(r"\{[A-Za-z_]+\}", value))


def _text(path: Path) -> str:
    data = path.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf"), f"{path} has a BOM"
    return data.decode("utf-8")


def _json(name: str):
    return json.loads(_text(SITE / name))


def _sql() -> str:
    """schema.sql lowercased with -- comments stripped and whitespace collapsed."""
    lines = [line.split("--", 1)[0] for line in _text(SCHEMA).splitlines()]
    return re.sub(r"\s+", " ", " ".join(lines)).lower()


def _committed_site_files() -> list[Path]:
    ignored = {"config.js"}
    return [
        p
        for p in SITE.rglob("*")
        if p.is_file()
        and p.name not in ignored
        and "node_modules" not in p.parts
        and p.suffix != ".woff2"
    ]


# --- words.json -----------------------------------------------------------------


def test_words_pool_shape():
    words = _json("words.json")
    assert isinstance(words, list)
    assert len(words) == 100
    ids = [w["id"] for w in words]
    assert len(set(ids)) == len(ids), "duplicate ids"
    assert len({w["word"].lower() for w in words}) == len(words), "duplicate words"
    required = {"id", "word", "hint", "category", "gendered"}
    for w in words:
        assert required <= set(w) <= required | {"gender_note"}, w
        assert KEBAB.match(w["id"]), w["id"]
        assert w["word"].strip() and w["hint"].strip(), w["id"]
        assert w["category"] in CATEGORIES, w["id"]
        assert isinstance(w["gendered"], bool), w["id"]
        if "gender_note" in w:
            assert w["gendered"] is True, w["id"]
            assert isinstance(w["gender_note"], str) and w["gender_note"].strip(), w["id"]


def test_words_are_english_ascii_only():
    for w in _json("words.json"):
        for field in ("id", "word", "hint", "gender_note"):
            if field not in w:
                continue
            value = w[field]
            assert value.isascii() and value.isprintable(), (w["id"], field)
            assert not ARABIC_RANGES.search(value), (w["id"], field)


def test_words_category_mix_and_gendered_rule():
    words = _json("words.json")
    by_id = {w["id"]: w for w in words}
    cats = {c: sum(w["category"] == c for w in words) for c in CATEGORIES}
    assert all(n >= 10 for n in cats.values()), cats
    gendered = {w["id"] for w in words if w["gendered"]}
    # Addressee or speaker dependent, including imperative buttons.
    assert {
        "are-you-sure",
        "welcome",
        "thank-you",
        "please",
        "you",
        "tired",
        "sorry",
        "save",
        "send",
        "delete",
        "cancel",
    } <= gendered
    # Greetings that change with the person addressed in some dialects.
    for wid in ("nice-to-meet-you", "good-luck", "goodbye"):
        assert wid in gendered, wid
        assert by_id[wid]["gender_note"].startswith("In some dialects"), wid
    # Nouns are not gendered.
    assert not {"settings", "password", "file", "folder", "database", "app"} & gendered
    # Near-duplicate pairs were reduced to one word each.
    removed = {"share-a-link", "submit", "continue", "confirm", "you-are-welcome"}
    assert not removed & set(by_id)
    assert "calendar date" in by_id["date"]["hint"]


# --- strings ---------------------------------------------------------------------


def test_strings_key_parity_and_arabic_placeholders():
    en = _json("strings.en.json")
    ar = _json("strings.ar.json")
    assert en and set(en) == set(ar)
    assert all(isinstance(v, str) and v.strip() for v in en.values())
    for key, value in ar.items():
        assert isinstance(value, str) and value.strip(), key
        assert ARABIC_RANGES.search(value), f"{key}: no Arabic letter"
        assert "TODO" not in value and AR_PLACEHOLDER not in value, key
        assert _placeholders(value) == _placeholders(en[key]), f"{key}: placeholders differ"
    assert "\ufffd" not in "".join(ar.values())
    for key in ("help_optional_identity", "identity_locked", "err_single_line", "mock_banner"):
        assert key in en, key
    assert "without your name or email" in en["mock_banner"]


def test_formula_message_explains_why():
    en = _json("strings.en.json")["err_formula"]
    ar = _json("strings.ar.json")["err_formula"]
    assert "formula" in en and "spreadsheet" in en and en.count(".") == 1
    assert all(c in en for c in "=+-@") and all(c in ar for c in "=+-@")


def test_arabic_review_lists_every_key():
    review = _text(SITE / "ARABIC_REVIEW.md")
    assert review.startswith("# AI draft: board review pending")
    for key in _json("strings.en.json"):
        assert f"| `{key}` |" in review, key


def test_arabic_review_records_intro_body_change():
    review = _text(SITE / "ARABIC_REVIEW.md")
    ar = _json("strings.ar.json")["intro_body"]
    old, new = "كلمة اختبار مفتوح المصدر يقيس", "كلمة معيار مفتوح يقيس"
    assert new in ar and old not in ar
    section = review.split("## Changes after the first draft")[1]
    assert old in section and new in section and "`intro_body`" in section


def test_progress_bar_has_accessible_name_from_localised_text():
    html = _text(SITE / "index.html")
    bar = re.search(r'<progress id="word-progress-bar"[^>]*>', html).group(0)
    label = re.search(r'aria-labelledby="([^"]+)"', bar)
    assert label, "progress bar needs aria-labelledby"
    assert f'id="{label.group(1)}"' in html
    for f in ("strings.en.json", "strings.ar.json"):
        assert "{current}" in _json(f)["word_progress"], f


def test_license_note_is_glued_for_display():
    js = _text(SITE / "js" / "i18n.js")
    assert "glueLicense(t(el.dataset.i18n))" in js


def test_country_strings_and_select():
    en = _json("strings.en.json")
    ar = _json("strings.ar.json")
    keys = {f"country_{c}" for c in COUNTRY_DIALECT}
    assert len(keys) == 22
    for k in keys | {"country_other", "country_placeholder", "label_country", "help_country"}:
        assert k in en and k in ar, k
        assert ARABIC_RANGES.search(ar[k]) and "TODO" not in ar[k], k
    assert not [k for k in en if k.startswith("dialect_") or k == "label_dialect"]
    assert en["label_country"] == "Which country's Arabic do you speak?"
    html = _text(SITE / "index.html")
    sel = re.search(r'<select id="f-country"[^>]*>(.*?)</select>', html, re.S)
    assert sel, "country select missing"
    assert re.search(r'<label for="f-country"', html), "label wired to the select"
    opts = re.findall(r'<option value="([^"]*)"([^>]*)>([^<]*)</option>', sel.group(1))
    assert opts[0][0] == "" and "disabled" in opts[0][1], "disabled placeholder first"
    codes = [v for v, _, _ in opts[1:]]
    assert codes[-1] == "other"
    assert codes[:-1] == list(COUNTRY_DIALECT), "same codes and order as the mapping"
    names = [en[f"country_{c}"] for c in codes[:-1]]
    assert names == sorted(names), "alphabetical by English name"
    logic = _text(SITE / "js" / "logic.js")
    for code, dialect in COUNTRY_DIALECT.items():
        assert f'  {code}: "{dialect}",' in logic, code


def test_html_i18n_keys_exist():
    en = _json("strings.en.json")
    html = _text(SITE / "index.html")
    used = set(re.findall(r'data-i18n(?:-aria-label)?="([^"]+)"', html))
    assert used and used <= set(en), used - set(en)
    js = "\n".join(_text(p) for p in (SITE / "js").glob("*.js"))
    for key in re.findall(r'\bt\("([a-z_-]+)"', js):
        assert key in en, key


def test_privacy_files():
    en = _text(SITE / "privacy.en.md")
    ar = _text(SITE / "privacy.ar.md")
    assert ARABIC_RANGES.search(ar) and "\ufffd" not in ar
    # Pending native wording is allowed only with the board marker (see ARABIC_REVIEW.md).
    assert ar.count("TODO") == ar.count("TODO(board): Arabic wording")
    for needle in (ISSUES_URL, "K-ABCDE-23456", "CC BY 4.0"):
        assert needle in ar, needle
    for prefix in ("# ", "## ", "- "):
        n_en = sum(line.startswith(prefix) for line in en.splitlines())
        n_ar = sum(line.startswith(prefix) for line in ar.splitlines())
        assert n_en == n_ar, (prefix, n_en, n_ar)
    for needle in (ISSUES_URL, "CC BY 4.0", "deletion code", "optional"):
        assert needle in en, needle
    assert not ARABIC_RANGES.search(en)


# --- schema.sql --------------------------------------------------------------------


def test_schema_rls_enabled_on_both_tables():
    sql = _sql()
    for table in ("contributors", "entries"):
        assert f"alter table public.{table} enable row level security" in sql
        assert f"alter table public.{table} force row level security" in sql


def test_schema_policies_are_insert_only_for_anon():
    sql = _sql()
    policies = re.findall(r"create policy (\w+) on public\.(\w+)(.*?)(?=;)", sql)
    assert len(policies) == 2
    for _name, _table, body in policies:
        assert "for insert" in body and "to anon" in body and "with check" in body
    for verb in ("select", "update", "delete", "all"):
        assert f"for {verb}" not in sql, verb
    assert "create view" not in sql and "create or replace view" not in sql
    assert "security definer" not in sql


def test_schema_grants_are_insert_only():
    sql = _sql()
    for table in ("contributors", "entries"):
        assert f"revoke all on table public.{table} from public, anon, authenticated" in sql
    grants = re.findall(r"\bgrant ([^;]*?) on (?:table )?(\S+) to (\w+)", sql)
    grants = [g for g in grants if g[1].startswith("public.")]
    assert len(grants) == 2
    for privs, table, role in grants:
        assert role == "anon", (table, role)
        assert privs.startswith("insert ("), privs
        assert "created_at" not in privs
        # No grant on the generated dialect column; the client sends country.
        cols = [c.strip() for c in privs[len("insert (") : privs.rindex(")")].split(",")]
        assert "dialect" not in cols and "dialect_other" not in cols, cols
        if table == "public.contributors":
            assert "country" in cols and "country_other" in cols, cols
    # Every function anon can execute is a pure helper in kilmeh_private.
    executable = re.findall(r"grant execute on function (\S+?)\(", sql)
    assert sorted(executable) == ["kilmeh_private.dialect_of", "kilmeh_private.text_ok"]
    assert "revoke all on function kilmeh_private.dialect_of(text) from public" in sql
    assert "grant select" not in sql and "grant update" not in sql and "grant delete" not in sql
    assert "grant all" not in sql
    # The helper function lives outside the exposed public schema.
    assert "revoke all on schema kilmeh_private from public" in sql
    assert "grant usage on schema kilmeh_private to anon" in sql
    assert (
        "revoke all on function kilmeh_private.text_ok(text, integer, boolean) from public" in sql
    )
    assert "grant execute on function kilmeh_private.text_ok(text, integer, boolean) to anon" in sql


def _section(sql: str, start: str, end: str) -> str:
    i = sql.index(start)
    return sql[i : sql.index(end, i + len(start))]


def _schema_parts() -> dict[str, str]:
    sql = _sql()
    policies = dict(re.findall(r"create policy (\w+) on public\.\w+(.*?)(?=;)", sql))
    return {
        "function": _section(sql, "create function kilmeh_private.text_ok", "$fn$;"),
        "contributors": _section(sql, "create table public.contributors", "create table"),
        "entries": _section(sql, "create table public.entries", "create index"),
        "contributors_policy": policies["contributors_anon_insert"],
        "entries_policy": policies["entries_anon_insert"],
    }


BS = chr(92)
_ESC = re.compile(re.escape(BS) + r"(?:u([0-9a-fA-F]{4})|U([0-9a-fA-F]{8}))")
_CLASS_BODY = r"((?:\[:space:\]|[^\]'])*)"
# Code points that must count as invisible (not visible text, hidden before a formula).
REQUIRED_INVISIBLE = (
    0x0009, 0x000A, 0x000B, 0x000C, 0x000D, 0x0020, 0x0085, 0x00A0, 0x00AD, 0x034F,
    0x061C, 0x115F, 0x1160, 0x1680, 0x180E, 0x200B, 0x200C, 0x200D, 0x200E, 0x200F,
    0x2028, 0x2029, 0x202A, 0x202E, 0x205F, 0x2066, 0x2069, 0x2800, 0x3000, 0x3164,
    0xFE00, 0xFE0F, 0xFEFF, 0xFFA0, 0xE0000, 0xE0041, 0xE007F,
)  # fmt: skip


def _merge(ranges):
    out: list[list[int]] = []
    for a, b in sorted(ranges):
        if out and a <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [tuple(r) for r in out]


def _sql_class_ranges(body: str):
    """Ranges named by a text_ok bracket class body, including [:space:]."""
    assert body.startswith("[:space:]"), body[:20]
    rest = body[len("[:space:]") :]
    ranges = [(0x09, 0x0D), (0x20, 0x20)]
    pos = 0
    tokens = []
    for m in _ESC.finditer(rest):
        assert m.start() == pos or rest[pos : m.start()] == "-", (pos, rest[pos : m.start()])
        tokens.append((m.group(1) or m.group(2), rest[pos : m.start()] == "-"))
        pos = m.end()
    assert pos == len(rest), rest[pos:]
    prev = None
    for hexs, is_range_end in tokens:
        cp = int(hexs, 16)
        if is_range_end:
            ranges.append((prev, cp))
            prev = None
        else:
            if prev is not None:
                ranges.append((prev, prev))
            prev = cp
    if prev is not None:
        ranges.append((prev, prev))
    return _merge(ranges)


def _sql_classes() -> tuple[str, str]:
    fn = _text(SCHEMA)
    visible = re.search(r"v ~ '\[\^" + _CLASS_BODY + r"\]'", fn)
    formula = re.search(r"v !~ '\^\[" + _CLASS_BODY + r"\]\*\[=\+@-\]'", fn)
    assert visible and formula, "text_ok classes not found"
    return visible.group(1), formula.group(1)


def _js_invisible_ranges():
    src = _text(SITE / "js" / "logic.js")
    block = re.search(r"INVISIBLE_RANGES = Object\.freeze\(\[(.*?)\]\);", src, re.S)
    assert block, "INVISIBLE_RANGES not found in logic.js"
    pairs = re.findall(r"\[0x([0-9a-f]+), 0x([0-9a-f]+)\]", block.group(1))
    assert pairs
    return _merge((int(a, 16), int(b, 16)) for a, b in pairs)


def test_schema_text_rule_function():
    fn = _schema_parts()["function"]
    assert "language sql immutable" in fn
    assert "security definer" not in fn
    assert "v is not null and char_length(v) between 1 and max_len" in fn
    visible, formula = _sql_classes()
    assert visible == formula, "visible rule and formula guard use one class"
    ranges = _sql_class_ranges(visible)
    for cp in REQUIRED_INVISIBLE:
        assert any(a <= cp <= b for a, b in ranges), hex(cp)
    # Real Arabic text parts are never in the class.
    for cp in (0x0640, 0x064B, 0x0651, 0x0627, 0x0041, 0x0030):
        assert not any(a <= cp <= b for a, b in ranges), hex(cp)
    # Single-line fields reject TAB, LF, VT, FF, CR, NEL, LS and PS anywhere.
    single = BS + "t" + BS + "n" + BS + "v" + BS + "f" + BS + "r"
    single += BS + "u0085" + BS + "u2028" + BS + "u2029"
    assert f"(not single_line or v !~ '[{single}]')" in _text(SCHEMA)
    assert f"/[{single}]/" in _text(SITE / "js" / "logic.js")


def test_js_and_sql_invisible_lists_are_identical():
    visible, _ = _sql_classes()
    assert _js_invisible_ranges() == _sql_class_ranges(visible)


# Every guarded text column, with (max length, single line), must use the rule in
# BOTH the table CHECK and the anon policy. Removing either side turns this red.
GUARDED = {
    "contributors": {"name": (100, True), "email": (254, True), "country_other": (100, True)},
    "entries": {
        "arabic": (200, False),
        "arabizi": (200, False),
        "arabic_feminine": (200, False),
        "arabizi_feminine": (200, False),
    },
}


def test_schema_every_text_column_is_guarded_in_table_and_policy():
    parts = _schema_parts()
    for table, cols in GUARDED.items():
        for col, (limit, single) in cols.items():
            call = f"kilmeh_private.text_ok({col}, {limit}, {str(single).lower()})"
            assert call in parts[table], (table, col, "table check")
            assert call in parts[f"{table}_policy"], (table, col, "policy")


def test_schema_constraints():
    sql = _sql()
    parts = _schema_parts()
    assert "check (consent = true)" in parts["contributors"]
    assert "consent = true" in parts["contributors_policy"]
    assert "consent boolean not null" in sql
    # Name and email are optional: nullable columns, checks apply only when present.
    assert re.search(r"\bname text,", sql) and re.search(r"\bemail text,", sql)
    assert "name is null or kilmeh_private.text_ok(name, 100, true)" in parts["contributors"]
    assert "email is null or ( kilmeh_private.text_ok(email, 254, true)" in parts["contributors"]
    assert "deletion_code text not null" in sql
    assert "unique (deletion_code)" in parts["contributors"]
    code_rule = "deletion_code ~ '^k-[2-9a-hjkmnp-tv-z]{5}-[2-9a-hjkmnp-tv-z]{5}$'"
    assert code_rule in parts["contributors"] and code_rule in parts["contributors_policy"]
    assert "credit_by_name boolean not null default false" in sql
    # credit_by_name needs a name: in the table CHECK and in the policy.
    credit = "credit_by_name = false or name is not null"
    assert f"check ( {credit} )" in parts["contributors"], "table check"
    assert f"({credit})" in parts["contributors_policy"], "policy"
    assert "dialect in ('" + "', '".join(DIALECTS) + "')" in sql
    assert "country_other is not null" in parts["contributors"]
    assert "dialect_other" not in sql


def test_schema_country_and_generated_dialect():
    sql = _sql()
    parts = _schema_parts()
    country_list = "country in ( " + ", ".join(f"'{c.lower()}'" for c in COUNTRY_DIALECT)
    country_list += ", 'other' )"
    assert f"check ( {country_list} )" in parts["contributors"], "table CHECK"
    assert country_list in parts["contributors_policy"], "policy"
    assert "country text not null" in parts["contributors"]
    # Dialect is derived by the database and can never disagree with country.
    assert (
        "dialect text not null generated always as (kilmeh_private.dialect_of(country)) stored"
        in parts["contributors"]
    )
    # The SQL mapping equals the agreed mapping, and is pure (reads no table).
    fn = _section(sql, "create function kilmeh_private.dialect_of", "$fn$;")
    assert "language sql immutable" in fn and "security definer" not in fn
    assert " from " not in fn.split("as $fn$", 1)[1]
    pairs = dict(re.findall(r"when '(\w+)' then '(\w+)'", fn))
    assert pairs == {**{c.lower(): d for c, d in COUNTRY_DIALECT.items()}, "other": "other"}
    # country_other: required iff country = 'other', in table and policy.
    assert "(country_other is null and country <> 'other')" in parts["contributors"]
    assert "(country <> 'other' and country_other is null)" in parts["contributors_policy"]
    assert "unique (contributor_id, word_id)" in sql
    assert "contributor_id uuid not null references public.contributors (id)" in sql
    assert "arabizi text not null" in parts["entries"]
    assert "id uuid primary key," in sql  # contributor id supplied by the client


# --- JS / HTML safety ------------------------------------------------------------


def _js_sources() -> list[Path]:
    return sorted((SITE / "js").glob("*.js")) + [SITE / "config.example.js"]


def test_js_has_no_html_sinks_or_eval():
    banned = re.compile(
        r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|\beval\s*\(|new Function"
        r"|setTimeout\(\s*['\"`]"
    )
    for path in _js_sources():
        assert not banned.search(_text(path)), path


def test_html_csp_and_no_inline_script():
    html = _text(SITE / "index.html")
    m = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)"', html)
    assert m, "CSP meta missing"
    csp = {d.split()[0]: d.split()[1:] for d in m.group(1).split(";") if d.strip()}
    assert csp["default-src"] == ["'none'"]
    assert csp["script-src"] == ["'self'"]
    assert csp["style-src"] == ["'self'"]
    assert csp["connect-src"] == ["'self'", f"https://{SUPABASE_REF}.supabase.co"]
    assert csp["form-action"] == ["'none'"]
    assert "unsafe-inline" not in m.group(1) and "unsafe-eval" not in m.group(1)
    # Every script is external and same-origin; no inline handlers or styles.
    for tag in re.findall(r"<script\b[^>]*>", html):
        assert re.search(r'src="js/[\w.-]+\.js(\?v=[\w.-]+)?"', tag), tag
    assert not re.search(r"<script\b[^>]*>\s*[^<\s]", html), "inline script body"
    assert not re.search(r"\son[a-z]+=", html)
    assert " style=" not in html and "<style" not in html
    assert "http://" not in html and "cdn" not in html.lower()


def test_html_and_js_handle_lang_and_dir():
    html = _text(SITE / "index.html")
    assert '<html lang="en" dir="ltr">' in html
    assert 'id="f-arabic" name="arabic" type="text" dir="rtl"' in html
    assert re.search(r'id="f-arabizi"[^>]*dir="ltr"', html)
    assert re.search(r'id="f-email"[^>]*dir="ltr"', html)
    i18n = _text(SITE / "js" / "i18n.js")
    assert "html.lang = lang" in i18n
    assert 'html.dir = lang === "ar" ? "rtl" : "ltr"' in i18n


def test_single_look_no_theme_switcher_left():
    banned = re.compile(r"data-theme|theme-choice|preview-bar|Preview only|\?theme|THEME_KEY")
    for name in ("index.html", "styles.css", "strings.en.json", "strings.ar.json"):
        assert not banned.search(_text(SITE / name)), name
    for path in (SITE / "js").glob("*.js"):
        text = _text(path)
        assert not banned.search(text) and "searchParams.set" not in text, path
        assert "kilmeh.contribute.theme" not in text, path


def test_fonts_are_referenced_licensed_and_small():
    css = _text(SITE / "styles.css")
    fonts = sorted((SITE / "fonts").glob("*.woff2"))
    assert fonts
    for font in fonts:
        assert f'url("fonts/{font.name}")' in css, f"{font.name} not used by styles.css"
        family = font.name.split("-")[0].capitalize()
        assert (SITE / "fonts" / f"OFL-{family}.txt").is_file(), f"licence for {font.name}"
    for licence in (SITE / "fonts").glob("OFL-*.txt"):
        family = licence.stem[4:].lower()
        assert any(f.name.startswith(family + "-") for f in fonts), f"{licence.name} unused"
        assert "SIL Open Font License" in _text(licence)
    for ref in re.findall(r'url\("fonts/([^"]+)"\)', css):
        assert (SITE / "fonts" / ref).is_file(), ref
    assert sum(f.stat().st_size for f in fonts) < 400_000


def test_css_uses_logical_properties_only():
    css = _text(SITE / "styles.css")
    physical = re.compile(
        r"(?<![\w-])(margin|padding|border)-(left|right)\b|(?<![\w-])(left|right)\s*:"
        r"|text-align\s*:\s*(left|right)|float\s*:\s*(left|right)"
    )
    assert not physical.search(css), physical.search(css)
    assert '[dir="rtl"] .icon-flip' in css


def test_no_secrets_and_config_is_ignored():
    gitignore = _text(SITE / ".gitignore")
    assert "config.js" in gitignore.split()
    example = _text(SITE / "config.example.js")
    assert "YOUR-PROJECT-REF" in example and "YOUR-ANON-PUBLIC-KEY" in example
    jwt = re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")
    key_like = re.compile(r"sb_(publishable|secret)_[A-Za-z0-9_-]{8,}|service_role\s*[:=]")
    for path in _committed_site_files():
        if path.suffix in {".png", ".ico"}:
            continue
        text = _text(path)
        assert not jwt.search(text), path
        assert not key_like.search(text), path
        other = r"https://(?!YOUR-PROJECT-REF|" + SUPABASE_REF + r")[a-z0-9]{20}\.supabase\.co"
        assert not re.search(other, text), path


def test_config_js_is_git_ignored():
    git = shutil.which("git")
    if git is None:
        pytest.skip("git not available")
    res = subprocess.run(
        [git, "check-ignore", "-q", str(SITE / "config.js")], cwd=ROOT, check=False
    )
    assert res.returncode == 0, "site/contribute/config.js must be git-ignored"


def test_site_text_files_are_utf8_without_bom_and_nfc_ascii_json():
    for path in _committed_site_files():
        text = _text(path)
        assert "\x00" not in text, path
        if path.suffix in {".json", ".js", ".css", ".html", ".sql"}:
            assert unicodedata.is_normalized("NFC", text), path


# --- JS unit tests via node --test (optional) --------------------------------------


def test_node_unit_tests():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not installed; JS logic covered only by structural checks")
    res = subprocess.run(
        # Explicit file: older Node (20) does not accept a directory after --test.
        [node, "--test", "tests/logic.test.js", "tests/api.test.js"],
        cwd=SITE,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert res.returncode == 0, res.stdout[-4000:] + res.stderr[-2000:]


def test_brand_order_is_fixed_latin_left_arabic_right():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    brand = re.search(
        r'<a class="brand" id="brand-home" href="./" dir="ltr">(.*?)</span></a>', html, re.S
    )
    assert brand, "brand wrapper must be direction-fixed (dir=ltr)"
    inner = brand.group(1)
    en = inner.index('class="brand-en"')
    ar = inner.index('class="brand-ar"')
    assert en < ar, "Latin brand must come before the Arabic one"
    assert 'lang="en"' in inner[en:ar] and 'lang="ar" dir="rtl"' in inner[ar:]
    css = (SITE / "styles.css").read_text(encoding="utf-8")
    assert ".brand-en::after" in css and ".brand-en::before" not in css


def test_logo_returns_to_sign_up_screen():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert '<a class="brand" id="brand-home" href="./"' in html
    app = (SITE / "js" / "app.js").read_text(encoding="utf-8")
    assert '$("brand-home").addEventListener("click", onHome)' in app
    body = re.search(r"function onHome\(event\) \{(.*?)\n\}", app, re.S).group(1)
    assert "preventDefault()" in body and 'state.screen = "intro"' in body
    assert "renderIntro()" in body and "if (sending) return" in body


def test_brand_star_is_jordan_heptagram():
    css = (SITE / "styles.css").read_text(encoding="utf-8")
    rule = re.search(r"\.brand-en::after \{(.*?)\}", css, re.S)
    assert rule, "star rule missing"
    poly = re.search(r"clip-path:\s*polygon\(([^)]*)\)", rule.group(1))
    assert poly, "star must be a clip-path polygon"
    pts = [tuple(float(v.rstrip("%")) for v in p.split()) for p in poly.group(1).split(",")]
    assert len(pts) == 14, "seven-pointed star has 14 vertices"
    assert pts[0] == (50.0, 0.0), "one point straight up"


def test_assets_are_versioned_and_consistent():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    versions = set(re.findall(r'(?:href="styles\.css|src="js/app\.js)\?v=([\w.-]+)"', html))
    assert len(versions) == 1, "index.html must version styles.css and js/app.js alike"
    (version,) = versions
    for js in sorted((SITE / "js").glob("*.js")):
        for spec in re.findall(r'from "(\./[^"]+)"', js.read_text(encoding="utf-8")):
            assert spec.endswith(f".js?v={version}"), f"{js.name}: unversioned import {spec}"


def test_module_specifiers_resolve_and_each_module_has_one_specifier():
    specs: dict[str, set[str]] = {}
    for js in sorted((SITE / "js").glob("*.js")):
        for spec in re.findall(r'from "(\./[^"]+)"', js.read_text(encoding="utf-8")):
            path = spec.split("?", 1)[0]
            assert (js.parent / path).is_file(), f"{js.name}: {spec} does not resolve"
            specs.setdefault(path, set()).add(spec)
    assert specs, "no module imports found"
    for path, variants in specs.items():
        # Two specifiers for one file would create two module instances with separate state.
        assert len(variants) == 1, f"{path} imported with several specifiers: {sorted(variants)}"


def test_no_placeholder_contact_left():
    for path in _committed_site_files():
        if path.suffix in {".png", ".ico"}:
            continue
        assert "CONTACT_EMAIL_PLACEHOLDER" not in _text(path), path


def test_notice_and_consent_versions_match():
    logic = _text(SITE / "js" / "logic.js")
    consent = re.search(r'CONSENT_TEXT_VERSION = "([\d-]+)"', logic).group(1)
    en = re.search(r"Notice version ([\d-]+)\.", _text(SITE / "privacy.en.md")).group(1)
    ar = re.search(r"([\d-]+)\.\s*$", _text(SITE / "privacy.ar.md")).group(1)
    assert consent == en == ar == "2026-11-12"


def test_new_privacy_arabic_is_listed_for_review():
    review = _text(SITE / "ARABIC_REVIEW.md")
    ar = _text(SITE / "privacy.ar.md")
    for heading in ("الجهة المسؤولة", "العمر", "الاستضافة", "أين توجد البيانات", "حقوقكم"):
        section = re.search(rf"## {heading}\n\n(.*?)(?=\n## )", ar, re.S).group(1)
        for line in section.strip().splitlines():
            parts = line.replace(" <!-- TODO(board): Arabic wording -->", "")
            # Pending sentences are English; the Arabic before them must still be listed.
            parts = re.split(r"(?=[A-Za-z])", parts, maxsplit=1)
            for part in parts:
                assert part.strip().lstrip("- ") in review, f"{heading}: not in ARABIC_REVIEW.md"


def test_brand_words_share_one_size_variable():
    css = (SITE / "styles.css").read_text(encoding="utf-8")
    brand = re.search(r"\.topbar > \.brand \{[^}]*--brand-fs:\s*clamp\([^;]*;[^}]*\}", css)
    assert brand, "--brand-fs (clamped, so both words shrink together) must be on .topbar > .brand"
    ar = re.search(r"\n\.brand-ar \{[^}]*font-size:\s*var\(--brand-fs\)", css)
    en = re.search(r"\.brand-en \{[^}]*font-size:\s*var\(--en-fs\)", css, re.S)
    assert ar and en, "both brand words must take their size from --brand-fs"
    assert re.search(r"--brand-fs:\s*clamp\(2\.1rem,[^;]*, 2\.6rem\);", css), (
        "Arabic: 2.1rem..2.6rem"
    )
    assert re.search(r"--en-fs:\s*min\(calc\(var\(--brand-fs\) \* 0\.944\)", css), "KILMEH ratio"


def test_no_email_address_in_site_files():
    """Contact goes through GitHub issues; no personal email in the site (board, 2026-11-22)."""
    for path in SITE.rglob("*"):
        if path.suffix not in {".md", ".html", ".js", ".json", ".css", ".sql", ".txt", ".yml"}:
            continue
        if "tests" in path.parts:
            continue
        text = _text(path)
        assert "proton" + ".me" not in text.lower(), path
        assert not EMAIL.search(text.replace("noreply.github.com", "")), path
