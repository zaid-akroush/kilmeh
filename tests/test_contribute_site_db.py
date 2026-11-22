"""Executes site/contribute/supabase/schema.sql against a real postgres:16 in Docker.

Opt-in: set KILMEH_DOCKER_TESTS=1 (needs the docker CLI and a running daemon, and
the postgres:16 image or network to pull it). Skipped otherwise. The container is
throwaway and removed at the end. Roles mimic Supabase: anon, authenticated and
service_role, with the default ALL grants on new public tables.

Non-ASCII test input is built from code points (see lit()) so this file stays ASCII.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site" / "contribute"
SCHEMA = SITE / "supabase" / "schema.sql"
BS = chr(92)
CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTVWXYZ"

pytestmark = pytest.mark.skipif(
    os.environ.get("KILMEH_DOCKER_TESTS") != "1",
    reason="set KILMEH_DOCKER_TESTS=1 to run the Postgres-in-Docker tests",
)


def cp(*points: int) -> str:
    return "".join(chr(p) for p in points)


def lit(value: str | None) -> str:
    """SQL literal for any text, using only ASCII in the statement (U& escapes)."""
    if value is None:
        return "null"
    out = []
    for ch in value:
        o = ord(ch)
        if ch == "'":
            out.append("''")
        elif ch == BS:
            out.append(BS + BS)
        elif 32 <= o < 127:
            out.append(ch)
        elif o <= 0xFFFF:
            out.append(BS + f"{o:04x}")
        else:
            out.append(BS + "+" + f"{o:06x}")
    return "U&'" + "".join(out) + "'"


_counter = {"n": 0}


def _next() -> int:
    _counter["n"] += 1
    return _counter["n"]


def code() -> str:
    """A fresh valid deletion code K-XXXXX-XXXXX."""
    n = _next()
    digits = []
    for _ in range(10):
        n, r = divmod(n, len(CODE_ALPHABET))
        digits.append(CODE_ALPHABET[r])
    s = "".join(reversed(digits))
    return f"K-{s[:5]}-{s[5:]}"


def word_id() -> str:
    return f"w{_next()}"


class Db:
    def __init__(self, name: str):
        self.name = name

    def run(self, sql: str, role: str | None = None) -> tuple[int, str]:
        prefix = f"set role {role};\n" if role else ""
        res = subprocess.run(
            ["docker", "exec", "-i", self.name, "psql", "-U", "postgres", "-d", "postgres"]
            + ["-v", "ON_ERROR_STOP=1", "-qtA"],
            input=prefix + sql,
            capture_output=True,
            text=True,
            check=False,
        )
        return res.returncode, (res.stdout + res.stderr).strip()

    def ok(self, sql: str, role: str | None = "anon") -> str:
        rc, out = self.run(sql, role)
        assert rc == 0, f"expected success, got: {out}\n{sql[:300]}"
        return out

    def bad(self, sql: str, role: str | None = "anon", needle: str = "") -> str:
        rc, out = self.run(sql, role)
        assert rc != 0, f"expected rejection, but it succeeded\n{sql[:300]}"
        assert "duplicate key" not in out, f"rejected for the wrong reason: {out}"
        assert needle in out, f"expected {needle!r} in: {out}"
        return out

    # --- row helpers -----------------------------------------------------------
    def contributor_sql(
        self,
        *,
        name=None,
        email=None,
        country="JO",
        country_other=None,
        credit=False,
        cid=None,
        deletion_code=None,
    ) -> str:
        cid_sql = f"'{cid}'" if cid else "gen_random_uuid()"
        return (
            "insert into contributors (id, name, email, country, country_other, consent,"
            " consent_text_version, deletion_code, credit_by_name) values "
            f"({cid_sql}, {lit(name)}, {lit(email)}, {lit(country)}, {lit(country_other)},"
            f" true, 'v1', {lit(deletion_code or code())}, {str(credit).lower()});"
        )

    def entry_sql(self, cid, *, arabic="x", arabizi="x", afem=None, zfem=None, kept=False) -> str:
        return (
            "insert into entries (contributor_id, word_id, arabic, arabizi, arabic_feminine,"
            " arabizi_feminine, kept_in_english) values "
            f"('{cid}', '{word_id()}', {lit(arabic)}, {lit(arabizi)}, {lit(afem)},"
            f" {lit(zfem)}, {str(kept).lower()});"
        )


@pytest.fixture(scope="module")
def db():
    if shutil.which("docker") is None:
        pytest.skip("docker CLI not found")
    name = f"kilmeh-schema-test-{uuid.uuid4().hex[:8]}"
    started = subprocess.run(
        ["docker", "run", "-d", "--name", name, "-e", "POSTGRES_PASSWORD=localonly", "postgres:16"],
        capture_output=True,
        text=True,
        check=False,
    )
    if started.returncode != 0:
        pytest.skip(f"cannot start postgres:16: {started.stderr.strip()[:200]}")
    try:
        for _ in range(90):
            ready = subprocess.run(
                ["docker", "exec", name, "psql", "-U", "postgres", "-qtAc", "select 1"],
                capture_output=True,
                text=True,
                check=False,
            )
            if ready.returncode == 0 and ready.stdout.strip() == "1":
                break
            time.sleep(1)
        else:
            pytest.fail("postgres did not become ready")
        d = Db(name)
        setup = """
            create role anon nologin;
            create role authenticated nologin;
            create role service_role nologin bypassrls;
            grant usage on schema public to anon, authenticated, service_role;
            alter default privileges in schema public
                grant all on tables to anon, authenticated, service_role;
        """
        d.ok(setup, role=None)
        d.ok(SCHEMA.read_text(encoding="utf-8"), role=None)
        yield d
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=False)


@pytest.fixture(scope="module")
def base_contributor(db):
    cid = str(uuid.uuid4())
    db.ok(db.contributor_sql(cid=cid, name="Base"), role="anon")
    return cid


AR = cp(0x0645, 0x0631, 0x062D, 0x0628, 0x0627)  # an Arabic word
# Invisible or format characters that must never count as visible text.
INVISIBLE_SAMPLES = {
    "ZWSP": cp(0x200B),
    "ZWJ+ZWNJ": cp(0x200D, 0x200C),
    "BOM": cp(0xFEFF),
    "NBSP": cp(0x00A0),
    "RLM LRM": cp(0x200F, 0x200E),
    "RLE PDF": cp(0x202B, 0x202C),
    "LRI PDI": cp(0x2066, 0x2069),
    "NEL": cp(0x0085),
    "ALM": cp(0x061C),
    "soft hyphen": cp(0x00AD),
    "CGJ": cp(0x034F),
    "Hangul filler": cp(0x115F, 0x1160),
    "Braille blank": cp(0x2800),
    "Hangul fill 3164": cp(0x3164),
    "halfwidth filler": cp(0xFFA0),
    "variation selector": cp(0xFE00, 0xFE0F),
    "tag characters": cp(0xE0000, 0xE0041, 0xE007F),
    "spaces and tab": " \t ",
}
LEADS = {
    "none": "",
    "space": " ",
    "tab": "\t",
    "ZWSP": cp(0x200B),
    "ALM": cp(0x061C),
    "soft hyphen": cp(0x00AD),
    "tag": cp(0xE0041),
    "variation selector": cp(0xFE0F),
    "Braille blank": cp(0x2800),
    "filler": cp(0x3164),
}


# --- access rules --------------------------------------------------------------------


def test_anon_can_insert_valid_rows(db, base_contributor):
    db.ok(db.contributor_sql(name="A Person", email="a@example.org", country="EG"))
    db.ok(db.contributor_sql())  # null name and email
    db.ok(db.contributor_sql(country="other", country_other="Chad"))
    db.ok(db.contributor_sql(name="Credit", credit=True))
    db.ok(db.entry_sql(base_contributor, arabic=AR, arabizi="m7bba"))
    db.ok(db.entry_sql(base_contributor, arabic=None, arabizi="app", kept=True))
    db.ok(db.entry_sql(base_contributor, afem=AR, zfem="a"))


def test_anon_cannot_read_change_or_delete(db, base_contributor):
    for table in ("contributors", "entries"):
        db.bad(f"select count(*) from {table};", needle="permission denied")
        db.bad(f"update {table} set created_at = now();", needle="permission denied")
        db.bad(f"delete from {table};", needle="permission denied")
        db.bad(f"truncate {table};", needle="permission denied")
    insert = db.entry_sql(base_contributor).rstrip(";") + " returning id;"
    db.bad(insert, needle="permission denied")  # RETURNING needs SELECT
    stamped = db.entry_sql(base_contributor).replace(
        "kept_in_english)", "kept_in_english, created_at)"
    )
    db.bad(stamped.replace("false);", "false, now());"), needle="permission denied")


def test_authenticated_and_service_role_cannot_insert(db, base_contributor):
    # No USAGE on kilmeh_private: the CHECK constraints call text_ok as the inserting role.
    for role in ("authenticated", "service_role"):
        db.bad(db.contributor_sql(), role=role, needle="permission denied")
        db.bad(db.entry_sql(base_contributor), role=role, needle="permission denied")
        db.bad(
            "select kilmeh_private.text_ok('a', 5, true);", role=role, needle="permission denied"
        )


def test_stored_arabic_text_is_byte_identical(db, base_contributor):
    inner = (
        AR[:2]
        + cp(0x200C)
        + AR[2:]
        + cp(0x200D, 0x064E, 0x0651, 0x0640, 0x061C, 0x200F, 0x2066)
        + "x"
        + cp(0x2069, 0xFE0F)
    )
    wid = word_id()
    db.ok(
        "insert into entries (contributor_id, word_id, arabic, arabizi) values "
        f"('{base_contributor}', '{wid}', {lit(inner)}, {lit('7' + cp(0xFE0F) + 'a')});"
    )
    stored = db.ok(
        "select encode(convert_to(arabic, 'UTF8'), 'hex'), "
        f"encode(convert_to(arabizi, 'UTF8'), 'hex') from entries where word_id = '{wid}';",
        role=None,
    )
    want = f"{inner.encode().hex()}|{('7' + cp(0xFE0F) + 'a').encode().hex()}"
    assert stored == want
    # Name with ZWNJ and tashkeel inside is accepted too.
    db.ok(db.contributor_sql(name=AR[:2] + cp(0x200C, 0x064E) + AR[2:]))


# --- the visible-character rule ------------------------------------------------------


def _text_column_cases(db, base_contributor):
    """(label, builder(value) -> sql) for every guarded text column."""
    return [
        ("name", lambda v: db.contributor_sql(name=v)),
        ("country_other", lambda v: db.contributor_sql(country="other", country_other=v)),
        ("arabic", lambda v: db.entry_sql(base_contributor, arabic=v, arabizi="x")),
        ("arabizi", lambda v: db.entry_sql(base_contributor, arabic="x", arabizi=v)),
        ("arabic_feminine", lambda v: db.entry_sql(base_contributor, afem=v)),
        ("arabizi_feminine", lambda v: db.entry_sql(base_contributor, zfem=v)),
    ]


def test_visible_character_rule(db, base_contributor):
    for column, build in _text_column_cases(db, base_contributor):
        db.ok(build("abc"))  # control: the same statement with real text is accepted
        for label, value in INVISIBLE_SAMPLES.items():
            out = db.bad(build(value))
            assert "violates" in out, (column, label, out)
    # email: invisible-only is never a valid address
    for label, value in INVISIBLE_SAMPLES.items():
        out = db.bad(db.contributor_sql(email=value))
        assert "violates" in out, ("email", label, out)
    db.ok(db.contributor_sql(email="a@x.org"))


SINGLE_LINE = {"name", "country_other"}


def test_formula_guard_on_every_text_column(db, base_contributor):
    for column, build in _text_column_cases(db, base_contributor):
        for lead_label, lead in LEADS.items():
            for first in "=+-@":
                out = db.bad(build(f"{lead}{first}cmd"))
                assert "violates" in out, (column, lead_label, first, out)
            if column in SINGLE_LINE and lead == "\t":
                continue  # a TAB is rejected anywhere in single-line fields
            # Same shape with real text first is accepted: the guard is the only difference.
            db.ok(build(f"{lead}a=cmd"))
    for lead_label, lead in LEADS.items():
        for first in "=+-@":
            out = db.bad(db.contributor_sql(email=f"{lead}{first}cmd@x.org"))
            assert "violates" in out, ("email", lead_label, first, out)
        if lead not in (" ", "\t"):  # whitespace never belongs in an email address
            db.ok(db.contributor_sql(email=f"{lead}a@x.org"))


def test_single_line_fields_reject_line_breaks_anywhere(db):
    breaks = {
        "TAB": "\t",
        "LF": "\n",
        "VT": cp(0x0B),
        "FF": cp(0x0C),
        "CR": "\r",
        "NEL": cp(0x0085),
        "LS": cp(0x2028),
        "PS": cp(0x2029),
    }
    for ch in breaks.values():
        db.bad(db.contributor_sql(name=f"a{ch}b"), needle="violates")
        db.bad(db.contributor_sql(email=f"a{ch}b@x.org"), needle="violates")
        db.bad(
            db.contributor_sql(country="other", country_other=f"a{ch}b"),
            needle="violates",
        )


# --- country and dialect ---------------------------------------------------------------


def _agreed_mapping() -> dict[str, str]:
    src = (SITE / "js" / "logic.js").read_text(encoding="utf-8")
    block = re.search(r"COUNTRY_DIALECT = Object\.freeze\(\{(.*?)\}\)", src, re.S)
    assert block, "COUNTRY_DIALECT not found"
    mapping = dict(re.findall(r'^\s+([A-Z]{2}): "(\w+)",', block.group(1), re.M))
    assert len(mapping) == 22
    return mapping


def test_country_maps_to_dialect_for_all_codes(db):
    mapping = _agreed_mapping()
    mapping["other"] = "other"
    for country, dialect in mapping.items():
        other = "Somewhere" if country == "other" else None
        dc = code()
        db.ok(db.contributor_sql(country=country, country_other=other, deletion_code=dc))
        stored = db.ok(f"select dialect from contributors where deletion_code = '{dc}';", role=None)
        assert stored == dialect, (country, stored, dialect)


def test_dialect_cannot_be_stored_explicitly_or_mismatched(db):
    base = (
        "insert into contributors (id, country, dialect, consent, consent_text_version,"
        " deletion_code) values (gen_random_uuid(), 'JO', 'gulf', true, 'v1', {c});"
    )
    db.bad(base.format(c=lit(code())), role="anon", needle="generated column")
    # Even the owner cannot write the generated column.
    db.bad(base.format(c=lit(code())), role=None, needle="generated column")
    dc = code()
    db.ok(db.contributor_sql(country="JO", deletion_code=dc))
    db.bad(
        f"update contributors set dialect = 'gulf' where deletion_code = '{dc}';",
        role=None,
        needle="generated column",
    )
    db.bad(
        f"update contributors set country = 'ZZ' where deletion_code = '{dc}';",
        role=None,
        needle="violates",
    )
    # Unknown country is rejected for anon.
    db.bad(db.contributor_sql(country="ZZ"), needle="violates")
