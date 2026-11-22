"""Probe: the reference prints junk to stdout at import and on every call. The worker sends the
agent's stdout to the discarded stderr, so the reference still scores 1.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("numerals.py")
path.write_text(
    'print("junk at import ]{", flush=True)\n'
    + path.read_text(encoding="utf-8")
    + """

_noisy_parse = parse_number


def parse_number(text):
    print("junk", flush=True)
    return _noisy_parse(text)
""",
    encoding="utf-8",
)
