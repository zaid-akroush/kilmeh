"""Language-ID grader: a known-good and a known-bad fixture per check, plus edge cases."""

import pytest

from kilmeh.graders.lang_id import EMPTY_DETAIL, check, comments, detect

# Neutral test strings, built from escapes, never prompts.
SALAM = "\u0645\u0631\u062d\u0628\u0627 \u0628\u0643\u0645"
BOOK = "\u0647\u0630\u0627 \u0643\u062a\u0627\u0628 \u062c\u0645\u064a\u0644"
EN = "this is a simple reply about a book"
DIGITS = "\u0661\u0662\u0663 \u0664\u0665"
W = "\u0643\u062a\u0627\u0628"  # one Arabic word
MIXED = f"{W} {W} one two three four"  # share 0.33
TECH1 = "\u062a\u0645 \u062a\u062d\u062f\u064a\u062b API \u0648 React"
TECH2 = (
    "\u0627\u0633\u062a\u062e\u062f\u0645 pip install requests "
    "\u062b\u0645 \u0634\u063a\u0644 \u0627\u0644\u0645\u0644\u0641"
)


def by_key(results):
    return {r.key: r for r in results}


@pytest.mark.parametrize(
    ("text", "want"),
    [
        (SALAM, "ar"),
        (EN, "en"),
        (MIXED, "mixed"),
        (f"{BOOK} `my_var.split()` {BOOK}", "ar"),  # code span ignored
        (f"{BOOK} get_user_name {BOOK} fooBar()", "ar"),  # identifiers ignored
        (f"{BOOK} https://example.com/some/long/path", "ar"),
        (f"{BOOK}\n```py\nprint('hello world again')\n```\n{BOOK}", "ar"),
        ("", "none"),
        ("   \n", "none"),
        (DIGITS, "none"),
        ("123 !!! 456", "none"),
    ],
)
def test_detect(text, want):
    assert detect(text) == want


def test_response_language_good_and_bad():
    assert by_key(check(SALAM))["response_language"].passed
    bad = by_key(check(EN))["response_language"]
    assert not bad.passed
    assert str(bad).startswith("FAIL response_language:")


def test_expected_en():
    assert by_key(check(EN, expected="en"))["response_language"].passed
    assert not by_key(check(SALAM, expected="en"))["response_language"].passed


def test_mixed_fails():
    assert not by_key(check(MIXED))["response_language"].passed


def test_empty_and_digits_fail_with_named_detail():
    for text in ("", DIGITS):
        r = by_key(check(text))["response_language"]
        assert not r.passed
        assert r.detail == EMPTY_DETAIL


PY_GOOD = f"x = 1  # {BOOK}\n# {SALAM}\ns = '# not a comment'\n"
PY_BAD = f"x = 1  # {EN}\n# {EN}\n"


def test_comments_language_good_and_bad():
    assert by_key(check(SALAM, source=PY_GOOD))["comments_language"].passed
    assert not by_key(check(SALAM, source=PY_BAD))["comments_language"].passed


def test_no_source_means_no_comments_key():
    assert [r.key for r in check(SALAM)] == ["response_language"]


def test_no_comments_fails_named():
    r = by_key(check(SALAM, source="x = 1\n"))["comments_language"]
    assert not r.passed
    assert r.detail == EMPTY_DETAIL


def test_python_comments():
    assert comments("a = '# no'  # yes\n# two\n", "py") == ["yes", "two"]


def test_python_broken_source_keeps_earlier_comments():
    assert comments("# one\nx = (\n", "py") == ["one"]


def test_js_comments():
    src = 'const u = "http://x.y"; // one\n/* two\n * three */\nlet s = `//no`;\n'
    assert comments(src, "js") == ["one", "two\n * three"]


def test_js_comments_check():
    good = f"let a = 1; // {BOOK}\n/* {SALAM} */\n"
    bad = f"let a = 1; // {EN}\n"
    assert by_key(check(SALAM, source=good, lang="js"))["comments_language"].passed
    assert not by_key(check(SALAM, source=bad, lang="ts"))["comments_language"].passed


def test_unsupported_lang():
    with pytest.raises(ValueError):
        comments("x", "rb")


def test_arabizi_counts_as_english():
    # Known limit: Arabizi is not detected.
    assert detect("marhaba kifak ya sadiq") == "en"


@pytest.mark.parametrize("text", [TECH1, TECH2, f"{BOOK} 3 \u00d7 4 \u00d7 5 \u00f7 2"])
def test_arabic_with_tech_words_and_math_signs_is_ar(text):
    assert detect(text) == "ar"


def test_english_with_one_arabic_quote_is_en():
    assert detect(f"{W} is the word you asked about in the book") == "en"


@pytest.mark.parametrize(
    ("n_ar", "n_en", "want"),
    [
        (1, 1, "ar"),  # share 0.5 exactly
        (4, 5, "mixed"),  # just under 0.5
        (1, 4, "en"),  # share 0.2 exactly
        (2, 7, "mixed"),  # just over 0.2
    ],
)
def test_threshold_boundaries(n_ar, n_en, want):
    assert detect(" ".join([W] * n_ar + ["word"] * n_en)) == want


def test_unclosed_fence_runs_to_end():
    assert detect(f"{BOOK}\n```py\nprint hello world again and again") == "ar"


def test_fail_detail_does_not_read_like_pass():
    bad = by_key(check(EN))["response_language"]
    good = by_key(check(SALAM))["response_language"]
    assert "not" in bad.detail and "not" not in good.detail


def test_bad_expected_raises():
    with pytest.raises(ValueError):
        check(SALAM, expected="fr")


def test_python_broken_source_scans_lines():
    src = "#!/usr/bin/env python\nx = (\ns = '# no'  # yes\n# noqa: E501\n# type: ignore\n# last\n"
    assert comments(src, "py") == ["yes", "last"]
