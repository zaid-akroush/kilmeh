# Requirements

The directory `/app` is a small JavaScript project (Node 22, ES modules, no dependencies). `src/money.js` has a stub `formatJOD(fils, locale)`; `src/receipt.js` uses it. Implement `formatJOD` in `src/money.js`.

The standard ICU/CLDR output (`Intl.NumberFormat`, `toLocaleString`) is not what is required here: for Jordan it differs in the symbol, the layout, the digits and the bidi marks, so it cannot be used as-is. Any method is fine as long as the output matches the strings below. The grader imports your module as an unprivileged user that cannot write to `/app` or read the grader, so don't write files at import time. `examples.mjs` has six examples (`node examples.mjs`); the grader uses many more inputs.

## `formatJOD(fils, locale) -> string`

`fils` is an amount in fils: 1 Jordanian dinar (JOD) = 1000 fils. It is a safe-integer `Number` or a `BigInt` of any size, and may be negative. Return a primitive `string`.

Throw a `RangeError` (or a subclass of it) when `fils` is a `Number` that is not a safe integer: a fraction (`1.5`), `NaN`, `Infinity` or `-Infinity`, or an integer beyond `Number.MAX_SAFE_INTEGER` in magnitude (`2 ** 53`). `-0` is the integer 0. Every `BigInt` is valid.

Let `N` be the amount in dinars written exactly as follows:

- the whole dinars (`fils` divided by 1000, dropping the sign), with a grouping separator between each group of three digits counted from the right (`999`, `1,000`, `1,234,567`; no separator below 1000);
- then the decimal separator and exactly three digits, the fils (`0.005`, `1.000`, `1,234.500`). Keep the trailing zeros. Never one, two or four decimals, never rounding.

The result is `N` in a layout chosen by `locale`, which is one of these three values:

| `locale` | Layout | Digits | Grouping | Decimal | Example for 1234500 fils |
|---|---|---|---|---|---|
| `"en-JO"` | `JD` + one space (U+0020) + `N` | `0`-`9` | `,` (U+002C) | `.` (U+002E) | `JD 1,234.500` |
| `"ar-JO"` | `N` + one space (U+0020) + `JD` | `0`-`9` | `,` | `.` | `1,234.500 JD` |
| `"ar-JO-u-nu-arab"` | same layout as `ar-JO` | Arabic-Indic, U+0660 to U+0669 (digit `n` is U+0660 plus `n`) | U+066C ARABIC THOUSANDS SEPARATOR | U+066B ARABIC DECIMAL SEPARATOR | U+0661 U+066C U+0662 U+0663 U+0664 U+066B U+0665 U+0660 U+0660, a space, `JD` |

The symbol `JD` is plain ASCII `J` and `D` in every locale.

- **Negative amounts** get a leading ASCII `-` (U+002D) before the whole result: `-JD 1,234.500` for `en-JO`, `-1,234.500 JD` for `ar-JO`, and `-` followed by the Arabic-Indic digits and `JD` for `ar-JO-u-nu-arab`. Zero has no sign (`JD 0.000`, `0.000 JD`).
- **No other marks:** no U+200E, U+200F, U+061C or any other bidi control character, and no non-breaking space, anywhere in the output.
- Results are exact for any size, so don't go through floating point: `formatJOD(123456789012345678901234567890n, "en-JO")` is `JD 123,456,789,012,345,678,901,234,567.890`, and `formatJOD(9007199254740991, "en-JO")` is `JD 9,007,199,254,740.991`.

## Keep `receipt.js` working

`receipt.receiptText(items, locale)` formats each item's line total and the grand total with `formatJOD` (it passes `BigInt` values). It must keep doing exactly that, so don't change its behaviour.
