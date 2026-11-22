"""Language-ID grader: does the agent answer and comment in the language it was asked in?

Standard library only. `detect(text)` labels text "ar", "en", "mixed" or "none" from the
share of Arabic words among Arabic plus Latin words (a word is a run of letters; it is
Arabic when it has more Arabic-script than Latin letters, so a bare tech word costs one word,
not its length). Other scripts are skipped. `comments(source, lang)`
pulls comment text out of Python or JS/TS. `check(text, expected, source=, lang=)` returns
one `Result` per check: `response_language`, plus `comments_language` when source is given.

Ignored before counting: fenced code blocks (an unclosed fence runs to the end), inline
`code`, URLs, and Latin tokens that look like code identifiers (snake_case, camelCase,
dotted or called names). Digits (including
Arabic-Indic), punctuation and other scripts are never letters here.

Empty or letterless input detects as "none", which never matches an expected language, so
the check FAILS with its own detail ("no letters to classify"). An agent that returns nothing
did not answer in Arabic. Same for source with no comments.

Limits: Arabizi (Arabic in Latin letters) is NOT detected; it counts as English. Plain
English words left outside backticks (a library name, a command) count as English. Short
texts swing the ratio fast. `check` raises ValueError when expected is not "ar" or "en".
Persian, Urdu and other Arabic-script languages count as "ar".
"""

from __future__ import annotations

import io
import re
import tokenize
from typing import NamedTuple

# Same Arabic ranges as text_integrity, restricted to letters at count time via str.isalpha.
_ARABIC = re.compile(
    "[\u0600-\u06ff\u0750-\u077f\u0870-\u08ff\ufb50-\ufdcf\ufdf0-\ufdff\ufe70-\ufefc]"
)
_LATIN = re.compile("[A-Za-z\u00c0-\u024f]")
_WORD = re.compile(r"[^\W\d_]+")
_STRIP = re.compile(
    r"```.*?```|```.*\Z|`[^`\n]*`|\bhttps?://\S+|\bwww\.\S+"
    r"|\b[A-Za-z0-9]*(?:_[A-Za-z0-9_]*|[a-z][A-Z][A-Za-z0-9]*|\.[A-Za-z_]\w*|\(\))\S*",
    re.S,
)

# ponytail: plain word-share cut-offs, the same for any length. Upgrade to length-aware
# scoring if very short replies (under ~5 words) misfire. Chosen so an Arabic sentence with
# a few bare tech words stays "ar" (>= 0.5) and an English reply quoting one Arabic word
# stays "en" (<= 0.2).
AR_MIN = 0.5  # Arabic word share at or above this -> "ar"
AR_MAX_EN = 0.2  # Arabic word share at or below this -> "en"; in between -> "mixed"

DETAIL = {
    "response_language": "response is written in the expected language",
    "comments_language": "code comments are written in the expected language",
}
FAIL_DETAIL = {
    "response_language": "response is not in the expected language",
    "comments_language": "code comments are not in the expected language",
}
EMPTY_DETAIL = "no letters to classify"


class Result(NamedTuple):
    key: str
    passed: bool
    detail: str

    def __str__(self) -> str:
        return f"{'PASS' if self.passed else 'FAIL'} {self.key}: {self.detail}"


def detect(text: str) -> str:
    """Return "ar", "en", "mixed" or "none" for text."""
    text = _STRIP.sub(" ", text)
    ar = en = 0
    for w in _WORD.findall(text):
        a = len(_ARABIC.findall(w))
        n = len(_LATIN.findall(w))
        ar += a > n
        en += n > a
    if ar + en == 0:
        return "none"
    share = ar / (ar + en)
    return "ar" if share >= AR_MIN else "en" if share <= AR_MAX_EN else "mixed"


_SKIP = re.compile(r"!|noqa\b|type:", re.I)  # shebang, noqa and type: pragmas


def _py_scan(source: str) -> list[str]:
    out: list[str] = []
    for line in source.splitlines():
        quote = ""
        for k, c in enumerate(line):
            if quote:
                quote = "" if c == quote else quote
            elif c in "'\"":
                quote = c
            elif c == "#":
                out.append(line[k + 1 :].strip())
                break
    return out


def _py_comments(source: str) -> list[str]:
    try:
        out = [
            t.string.lstrip("#").strip()
            for t in tokenize.generate_tokens(io.StringIO(source).readline)
            if t.type == tokenize.COMMENT
        ]
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # ponytail: line scan, fooled by multi-line strings; only used on broken source
        out = _py_scan(source)
    return [c for c in out if not _SKIP.match(c)]


def _js_comments(source: str) -> list[str]:
    # ponytail: regex literals (quotes and apostrophes inside them) and template ${} nesting
    # are not parsed; a quote in a regex literal can swallow later comments.
    out: list[str] = []
    i, n = 0, len(source)
    while i < n:
        c = source[i]
        two = source[i : i + 2]
        if two == "//":
            j = source.find("\n", i)
            j = n if j < 0 else j
            out.append(source[i + 2 : j].strip())
            i = j
        elif two == "/*":
            j = source.find("*/", i + 2)
            j = n if j < 0 else j
            out.append(source[i + 2 : j].strip(" *\n\t"))
            i = j + 2
        elif c in "'\"`":  # skip strings so "http://x" is not a comment
            i += 1
            while i < n and source[i] != c:
                i += 2 if source[i] == "\\" else 1
            i += 1
        else:
            i += 1
    return out


def comments(source: str, lang: str) -> list[str]:
    """Comment texts, in order. lang is "py" or "js" (also "ts")."""
    if lang == "py":
        return _py_comments(source)
    if lang in ("js", "ts"):
        return _js_comments(source)
    raise ValueError(f"unsupported lang: {lang!r}")


def _result(key: str, text: str, expected: str) -> Result:
    found = detect(text)
    if found == "none":
        return Result(key, False, EMPTY_DETAIL)
    ok = found == expected
    return Result(key, ok, DETAIL[key] if ok else FAIL_DETAIL[key])


def check(
    text: str, expected: str = "ar", *, source: str | None = None, lang: str = "py"
) -> list[Result]:
    """Check the response text and, when source is given, its comments."""
    if expected not in ("ar", "en"):
        raise ValueError(f"expected must be 'ar' or 'en', got {expected!r}")
    results = [_result("response_language", text, expected)]
    if source is not None:
        joined = "\n".join(comments(source, lang))
        results.append(_result("comments_language", joined, expected))
    return results
