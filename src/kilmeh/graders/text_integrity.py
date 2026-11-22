"""Text-integrity grader: did an edit damage the Arabic text of a file?

Standard library only. `check(original, edited)` takes the raw bytes before and after the
edit and returns one `Result` per check. Inputs are never normalized or reordered; every
comparison reads the decoded code points as they are.

Span choice: the "Arabic text" of a file is its Arabic-script characters (the Arabic blocks
and presentation forms, minus U+061C) in order, concatenated. Joiners, bidi controls and
everything else (Latin, digits, whitespace, markup) are outside the spans, so they have their
own checks and the surrounding code may change freely. Concatenating, rather than comparing
span by span, keeps a deleted ZWNJ (which would merge two runs) a joiner failure only.
Consequence: any change to an Arabic character, including NFC/NFD drift, also fails byte_exact.

Limits: sequences are checked, positions are not (moved Arabic, bidi controls or joiners
pass). Line endings are not checked (CRLF passes). no_mojibake is a heuristic: "\u00d8" followed
by U+0080-00BF can false-fail.
"""

from __future__ import annotations

import re
import unicodedata
from typing import NamedTuple

# Arabic, Supplement, Extended-A/B, presentation forms A (minus noncharacters U+FDD0-FDEF) and B
# (not U+FEFF, the BOM), Mathematical Alphabetic Symbols, Rumi.
_ARABIC = re.compile(
    "[\u0600-\u06ff\u0750-\u077f\u0870-\u08ff\ufb50-\ufdcf\ufdf0-\ufdff\ufe70-\ufefc"
    "\U00010e60-\U00010e7f\U0001ee00-\U0001eeff]"
)
_BIDI = re.compile("[\u200e\u200f\u061c\u202a-\u202e\u2066-\u2069]")
_JOINERS = re.compile("[\u200c\u200d]")
# A lead byte of Arabic in UTF-8 (0xD8-0xDB) read as cp1252/latin-1 gives Ø Ù Ú Û, followed
# by a continuation byte (0x80-0xBF) shown as latin-1 or cp1252 text.
_MOJIBAKE = re.compile(
    "[\u00d8-\u00db][\u0080-\u00bf\u0152\u0153\u0160\u0161\u0178\u017d\u017e\u0192\u02c6\u02dc"
    "\u2013-\u203a\u20ac\u2122]"
)

DETAIL = {
    "valid_utf8": "edited file decodes as UTF-8",
    "no_bom_added": "edited file does not start with a UTF-8 BOM the original lacked",
    "byte_exact": "Arabic-script characters are identical, in order",
    "normalization_unchanged": "Arabic text keeps its NFC/NFD/NFKC status",
    "bidi_controls_kept": "bidi control characters have the same sequence",
    "joiners_kept": "ZWJ and ZWNJ have the same sequence",
    "no_mojibake": "no U+FFFD or cp1252/latin-1 double-encoding added",
}


class Result(NamedTuple):
    key: str
    passed: bool
    detail: str

    def __str__(self) -> str:
        return f"{'PASS' if self.passed else 'FAIL'} {self.key}: {self.detail}"


def _decode(data: bytes) -> str:
    # surrogateescape: a bad byte becomes a lone surrogate, not U+FFFD (only valid_utf8 fails)
    return data.decode("utf-8", errors="surrogateescape")


def _arabic(text: str) -> str:
    return "".join(c for c in _ARABIC.findall(text) if c != "\u061c")


def _forms(text: str) -> tuple[bool, ...]:
    return tuple(unicodedata.normalize(f, text) == text for f in ("NFC", "NFD", "NFKC"))


def _mojibake(text: str) -> int:
    return len(_MOJIBAKE.findall(text)) + text.count("\ufffd")


def check(original: bytes, edited: bytes) -> list[Result]:
    """Compare original and edited file bytes; one Result per check, in a fixed order."""
    o, e = _decode(original), _decode(edited)
    ao, ae = _arabic(o), _arabic(e)
    try:
        edited.decode("utf-8")
        utf8_ok = True
    except UnicodeDecodeError:
        utf8_ok = False
    bom = b"\xef\xbb\xbf"
    outcomes = {
        "valid_utf8": utf8_ok,
        "no_bom_added": not (edited.startswith(bom) and not original.startswith(bom)),
        "byte_exact": ae == ao,
        "normalization_unchanged": _forms(ae) == _forms(ao),
        "bidi_controls_kept": _BIDI.findall(e) == _BIDI.findall(o),
        "joiners_kept": _JOINERS.findall(e) == _JOINERS.findall(o),
        "no_mojibake": _mojibake(e) <= _mojibake(o),
    }
    return [Result(k, outcomes[k], DETAIL[k]) for k in DETAIL]
