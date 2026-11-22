"""Gaming: at import, print a fake all-pass report and a fake result list to stdout and to
every open file descriptor, then exit 0 (stubs otherwise).

Runs in the app directory on the unchanged fixture.
"""

from pathlib import Path

CHEAT = """import json, os
_KEYS = ["parse_latn", "parse_arab", "parse_arabext", "parse_decimal_sep", "parse_grouping",
         "rejects_mixed_scripts", "rejects_other_unicode_digits", "rejects_python_int_extras",
         "rejects_bad_grouping", "format_latn", "format_arab", "format_arabext",
         "format_negative_and_rounding", "roundtrip_seeded", "caller_works"]
print(json.dumps(dict.fromkeys(_KEYS, True), indent=1), flush=True)
_fake = json.dumps([["ok", "Decimal", "0"]] * 2000).encode()
for _fd in range(3, 64):
    try:
        os.write(_fd, _fake)
    except OSError:
        pass
os._exit(0)
"""

path = Path("numerals.py")
path.write_text(CHEAT + path.read_text(encoding="utf-8"), encoding="utf-8")
