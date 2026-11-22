"""Validate the Arabizi answer key under `data/arabizi/` (never rewrites or normalises text)."""

import hashlib
import json
import unicodedata
from pathlib import Path

DIALECTS = {"levantine", "gulf", "egyptian", "maghrebi", "iraqi", "sudanese", "other"}
SOURCES = {"board", "site"}
KEY_REQUIRED = ("id", "arabizi", "arabic", "dialect", "country", "source", "authors")
KEY_OPTIONAL = ("alt_arabic", "notes")
TEMPLATE_FIELDS = ("id", "scenario", "arabizi", "arabic")
CONTROL_FIELDS = ("arabizi", "arabic", "alt_arabic", "scenario")
SPLIT_THRESHOLD = 51  # first byte of sha256(id) < 51 -> test (about 20%)
_ARABIC_SCRIPT = (
    (0x0600, 0x06FF),
    (0x0750, 0x077F),
    (0x08A0, 0x08FF),
    (0xFB50, 0xFDFF),
    (0xFE70, 0xFEFF),
)


def split_of(pair_id: str) -> str:
    """The split an id belongs to: 'test' if sha256(id as UTF-8)[0] < 51, else 'train'."""
    first = hashlib.sha256(pair_id.encode("utf-8")).digest()[0]
    return "test" if first < SPLIT_THRESHOLD else "train"


def has_arabic_letter(text: str) -> bool:
    return any(unicodedata.name(c, "").startswith("ARABIC LETTER") for c in text)


def has_arabic_script(text: str) -> bool:
    return any(lo <= ord(c) <= hi for c in text for lo, hi in _ARABIC_SCRIPT)


def _read_lines(path: Path, errs: list[str]) -> list[tuple[int, str]]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        errs.append(f"{path}:1: file starts with a BOM")
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        errs.append(f"{path}: not valid UTF-8 ({e.reason} at byte {e.start})")
        return []
    if "\r" in text:
        errs.append(f"{path}: contains CR; line endings must be LF only")
        text = text.replace("\r", "")
    return list(enumerate(text.split("\n"), 1))


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    keys = [k for k, _ in pairs]
    for k in keys:
        if keys.count(k) > 1:
            raise ValueError(f"duplicate key '{k}'")
    return dict(pairs)


def _check_chars(where: str, row: dict, errs: list[str]) -> bool:
    """Reject lone surrogates and C0/DEL control characters. True if the row is unusable."""
    bad = False
    for field, value in row.items():
        strings = value if isinstance(value, list) else [value]
        for s in strings:
            if not isinstance(s, str):
                continue
            try:
                s.encode("utf-8")
            except UnicodeEncodeError:
                errs.append(f"{where} field '{field}': contains a lone surrogate")
                bad = True
                continue
            if field in CONTROL_FIELDS and any(ord(c) < 0x20 or ord(c) == 0x7F for c in s):
                errs.append(f"{where} field '{field}': contains a control character")
    return bad


def _check_text(where: str, row: dict, template: bool, errs: list[str]) -> None:
    for field in ("arabizi", "arabic"):
        value = row.get(field)
        if field not in row:
            continue
        if not isinstance(value, str):
            errs.append(f"{where} field '{field}': must be a string")
        elif not value.strip() and not template:
            errs.append(f"{where} field '{field}': must not be empty")
    arabizi, arabic = row.get("arabizi"), row.get("arabic")
    if isinstance(arabizi, str) and has_arabic_script(arabizi):
        errs.append(f"{where} field 'arabizi': contains Arabic-script characters")
    if isinstance(arabic, str) and arabic.strip() and not has_arabic_letter(arabic):
        errs.append(f"{where} field 'arabic': contains no Arabic letter")


def _check_key_row(where: str, row: dict, errs: list[str]) -> None:
    for f in sorted(set(row) - set(KEY_REQUIRED) - set(KEY_OPTIONAL)):
        errs.append(f"{where} field '{f}': unknown field")
    for f in KEY_REQUIRED:
        if f not in row:
            errs.append(f"{where} field '{f}': missing")
    _check_text(where, row, False, errs)
    if "dialect" in row and row["dialect"] not in DIALECTS:
        errs.append(f"{where} field 'dialect': must be one of {sorted(DIALECTS)}")
    if "source" in row and row["source"] not in SOURCES:
        errs.append(f"{where} field 'source': must be one of {sorted(SOURCES)}")
    if "authors" in row and (type(row["authors"]) is not int or row["authors"] not in (1, 2)):
        errs.append(f"{where} field 'authors': must be 1 or 2")
    if "country" in row and not (isinstance(row["country"], str) and row["country"].strip()):
        errs.append(f"{where} field 'country': must be a non-empty string")
    if "notes" in row and not isinstance(row["notes"], str):
        errs.append(f"{where} field 'notes': must be a string")
    if "alt_arabic" in row:
        alt = row["alt_arabic"]
        if not isinstance(alt, list) or not all(
            isinstance(a, str) and has_arabic_letter(a) for a in alt
        ):
            errs.append(f"{where} field 'alt_arabic': must be a list of Arabic strings")


def _check_template_row(where: str, row: dict, errs: list[str]) -> None:
    for f in sorted(set(row) - set(TEMPLATE_FIELDS)):
        errs.append(f"{where} field '{f}': unknown field")
    for f in TEMPLATE_FIELDS:
        if f not in row:
            errs.append(f"{where} field '{f}': missing")
    if "scenario" in row and not isinstance(row["scenario"], str):
        errs.append(f"{where} field 'scenario': must be a string")
    _check_text(where, row, True, errs)


def _check_file(path: Path, kind: str, seen: dict[str, str], errs: list[str]) -> None:
    """kind is 'train', 'test' or 'template'."""
    lines = _read_lines(path, errs)
    if lines and lines[-1][1] == "":
        lines.pop()  # trailing newline
    for n, line in lines:
        where = f"{path}:{n}:"
        if not line.strip():
            errs.append(f"{where} blank line")
            continue
        try:
            row = json.loads(line, object_pairs_hook=_no_duplicate_keys)
        except json.JSONDecodeError as e:
            errs.append(f"{where} invalid JSON ({e.msg})")
            continue
        except ValueError as e:
            errs.append(f"{where} invalid JSON ({e})")
            continue
        if not isinstance(row, dict):
            errs.append(f"{where} line must be a JSON object")
            continue
        if _check_chars(where, row, errs):
            continue
        if kind == "template":
            _check_template_row(where, row, errs)
        else:
            _check_key_row(where, row, errs)
        pid = row.get("id")
        if not isinstance(pid, str) or not pid.strip():
            if "id" in row:
                errs.append(f"{where} field 'id': must be a non-empty string")
            continue
        if pid != pid.strip():
            errs.append(f"{where} field 'id': must not have leading or trailing whitespace")
            continue
        if pid in seen:
            errs.append(f"{where} field 'id': duplicate id '{pid}' (first at {seen[pid]})")
        else:
            seen[pid] = f"{path}:{n}"
        if kind != "template" and split_of(pid) != kind:
            errs.append(
                f"{where} field 'id': '{pid}' belongs in {split_of(pid)}.jsonl, "
                f"found in {kind}.jsonl"
            )


def validate_arabizi(root: Path) -> tuple[int, list[str]]:
    """Return (pairs checked, errors) for the key layout under root."""
    errs: list[str] = []
    seen: dict[str, str] = {}
    if not root.is_dir():
        return 0, [f"{root}: not a directory"]
    files: list[tuple[Path, str]] = []
    for path in sorted((root / "key").glob("*/*")):
        if path.name in ("train.jsonl", "test.jsonl"):
            files.append((path, path.stem))
        elif path.is_file():
            errs.append(f"{path}: unexpected file (key versions hold train.jsonl and test.jsonl)")
    files += [(p, "template") for p in sorted((root / "template").glob("*.jsonl"))]
    base = root.resolve()
    for path, kind in files:
        if path.is_symlink():
            errs.append(f"{path}: symlinks are not allowed")
        elif not path.resolve().is_relative_to(base):
            errs.append(f"{path}: resolves outside {root}")
        else:
            _check_file(path, kind, seen, errs)
    return len(seen), errs
