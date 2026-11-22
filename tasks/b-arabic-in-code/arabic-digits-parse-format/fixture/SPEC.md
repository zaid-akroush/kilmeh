# Requirements

The directory `/app` is a small Python project. `numerals.py` has two stub functions, `parse_number` and `format_number`; `invoice.py` uses them. Implement both functions in `numerals.py`.

Use only the Python standard library: the grader imports your module without site-packages. It runs your code as an unprivileged user that cannot write to `/app` or read the grader, so don't write files at import time. `test_numerals.py` has six examples (`python3 test_numerals.py`); the grader uses many more inputs than these.

## Digit systems

| Name | Digits | Grouping separator | Decimal separator |
|---|---|---|---|
| `latn` | `0`-`9` (U+0030 to U+0039) | `,` (U+002C) | `.` (U+002E) |
| `arab` (Arabic-Indic) | U+0660 to U+0669 | U+066C ARABIC THOUSANDS SEPARATOR | U+066B ARABIC DECIMAL SEPARATOR; `parse_number` also accepts `.` |
| `arabext` (Extended Arabic-Indic) | U+06F0 to U+06F9 | U+066C | U+066B; `parse_number` also accepts `.` |

Digit `n` of each system is the system's first code point plus `n` (U+0660 is 0, U+0669 is 9, U+06F5 is 5).

## `parse_number(text: str) -> Decimal`

Return a `decimal.Decimal` (exactly that type, not a subclass) whose value equals the written number. Only the value is compared, so `Decimal("10.25")` and `Decimal("10.250")` are both fine.

First remove leading and trailing ASCII spaces (U+0020 only). What remains must be exactly:

```
[-] INTEGER [DECIMAL_SEPARATOR FRACTION]
INTEGER  = one or more digits                         (no grouping), or
           1 to 3 digits, then one or more groups of   (grouping separator + exactly 3 digits)
FRACTION = one or more digits
```

- The sign is an optional single `-` (U+002D HYPHEN-MINUS) at the very start. No `+`, no U+2212 MINUS SIGN, no space after the `-`.
- Every digit comes from one system, and every separator must belong to that same system: Western digits take `,` and `.`; Arabic-Indic and Extended Arabic-Indic digits take U+066C and either U+066B or `.`.
- Leading zeros are allowed (`007` is 7). Grouping is optional, but when it is used it must be exact. There can be any number of groups. There is never grouping in the fraction. A decimal separator needs at least one digit on each side.
- Results are exact for any length, so don't go through `float`.

Raise `ValueError` (or a subclass of it) for anything else, including:

- **Mixed systems:** Western with Arabic-Indic digits (`1` followed by U+0662), Arabic-Indic with Extended digits (U+0661 followed by U+06F2), Western digits with U+066B or U+066C, and Eastern digits with `,`.
- **Digits of any other system:** Devanagari, Bengali, Thai, NKo, fullwidth (U+FF11), mathematical (U+1D7CF), superscript (U+00B2) and circled (U+2460) digits.
- **What Python's `int()` or `Decimal()` would accept:** an empty or all-space string, a lone `-`, underscores (`1_000`), inner spaces (`1 000`, `- 5`), `+5`, exponents (`1e3`), `NaN`, `inf` and `Infinity`, `.5`, `5.`, `--5`, `5-`, `0x10`, and any whitespace that is not a leading or trailing U+0020 (tab, newline, U+00A0 NO-BREAK SPACE).
- **Bad grouping:** `1,23`, `12,34,567`, `1,2345`, `,123`, `123,`, `1,,234`, `1234,567`, `1,234,56`, `1.234,5`, `1,234.567,8`, `1,234.` (and the same shapes in Eastern digits).

## `format_number(value, system: str, places: int = 0) -> str`

`value` is an `int` or a `Decimal`, `system` is `"latn"`, `"arab"` or `"arabext"`, and `places` is an int of 0 or more. Return a `str` (exactly that type, not a subclass):

1. Round `value` to exactly `places` decimal places with `ROUND_HALF_EVEN` (2.5 gives 2, 3.5 gives 4, `Decimal("1.005")` at 2 places gives 1.00). Be exact at any magnitude; don't use `float`.
2. Group the integer part in threes from the right with the system's grouping separator, always: `1,000`, `1,234`, `999` (no separator below 1000).
3. If `places > 0`, add the system's decimal separator (`.` for `latn`, U+066B for `arab` and `arabext`, never `.` for those) and exactly `places` digits, keeping trailing zeros. If `places == 0`, add no decimal separator.
4. Write every digit in the system's digits.
5. A negative result starts with `-` (U+002D) and has no other mark: no U+061C, U+200E, U+200F or other bidi characters anywhere. If the rounded value is zero, there is no sign (`Decimal("-0.004")` at 2 places gives `0.00`, and `Decimal("-0.5")` at 0 places gives `0`).

Examples: `format_number(Decimal("1234567.891"), "latn", 2)` gives `1,234,567.89`; `format_number(Decimal("12.5"), "latn", 3)` gives `12.500`; `format_number(Decimal("42.9"), "latn")` gives `43`; `format_number(-1000000, "arabext")` gives `-` followed by U+06F1 U+066C U+06F0 U+06F0 U+06F0 U+066C U+06F0 U+06F0 U+06F0.

For any value `x` with at most `places` decimals, `parse_number(format_number(x, system, places))` must equal `x`.

## Keep `invoice.py` working

`invoice.total_text(amounts, system)` sums the amounts (each one parsed with `parse_number`, each in any one system) and formats the total with `format_number(total, system, 2)`. It must keep doing exactly that, so don't change its behaviour.
