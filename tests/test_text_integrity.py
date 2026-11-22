"""Text-integrity grader: a known-good fixture and one known-bad fixture per check."""

import pytest

from kilmeh.graders.text_integrity import DETAIL, check

# Neutral test strings, built from escapes, never prompts.
SALAM = "\u0645\u0631\u062d\u0628\u0627"
BOOK = "\u0643\u062a\u0627\u0628"
MADDA = "\u0622"  # alef with madda, precomposed (NFC)
LRM, RLM, ALM = "\u200e", "\u200f", "\u061c"
ZWNJ, ZWJ = "\u200c", "\u200d"

ORIGINAL = (
    f's = "{SALAM}{RLM} {BOOK[:2]}{ZWNJ}{BOOK[2:]} {MADDA}{ZWJ}{LRM}{ALM}"\nprint(s)  # keep\n'
)


def enc(text: str) -> bytes:
    return text.encode("utf-8")


def failing(edited: bytes) -> set[str]:
    return {r.key for r in check(enc(ORIGINAL), edited) if not r.passed}


def test_known_good_passes_everything():
    results = check(enc(ORIGINAL), enc(ORIGINAL))
    assert [r.key for r in results] == list(DETAIL)
    assert all(r.passed for r in results)
    assert str(results[0]) == "PASS valid_utf8: edited file decodes as UTF-8"


def test_non_arabic_edits_are_allowed():
    edited = ORIGINAL.replace("print(s)  # keep", "print(s.strip())  # changed\nx = 1")
    assert failing(enc(edited)) == set()


BAD = {
    "valid_utf8": enc(ORIGINAL) + b"\xff",
    "no_bom_added": b"\xef\xbb\xbf" + enc(ORIGINAL),
    "byte_exact": enc(ORIGINAL.replace(SALAM, SALAM[:-1])),
    "normalization_unchanged": enc(ORIGINAL.replace(MADDA, "\u0627\u0653")),
    "bidi_controls_kept": enc(ORIGINAL.replace(LRM, "")),
    "joiners_kept": enc(ORIGINAL.replace(ZWNJ, "")),
    "no_mojibake": enc(ORIGINAL + "# \u00d8\u00a7\n"),
}


def test_bad_fixtures_cover_every_check():
    assert set(BAD) == set(DETAIL)


@pytest.mark.parametrize("key", list(BAD))
def test_known_bad_fails_exactly_that_check(key):
    expected = {key}
    if key == "normalization_unchanged":
        expected.add("byte_exact")  # a drifted code point is also a byte change
    assert failing(BAD[key]) == expected


@pytest.mark.parametrize("ch", ["\u0870", "\U0001ee00"])
def test_extended_arabic_blocks_are_spans(ch):
    original = enc(ORIGINAL + f"# {ch}\n")
    edited = enc(ORIGINAL + f"# {chr(ord(ch) + 1)}\n")
    assert {r.key for r in check(original, edited) if not r.passed} == {"byte_exact"}


def test_latin_o_slash_words_pass():
    # "Øresund Ørsted Øl"
    assert failing(enc(ORIGINAL + "# \u00d8resund \u00d8rsted \u00d8l\n")) == set()


def test_replacement_char_is_mojibake():
    assert failing(enc(ORIGINAL + "# \ufffd\n")) == {"no_mojibake"}


def test_existing_mojibake_in_original_is_not_blamed():
    original = enc(ORIGINAL + "# \u00d8\u00a7\n")
    assert all(r.passed for r in check(original, original))


def test_bidi_reorder_fails():
    edited = ORIGINAL.replace(f"{LRM}{ALM}", f"{ALM}{LRM}")
    assert failing(enc(edited)) == {"bidi_controls_kept"}
