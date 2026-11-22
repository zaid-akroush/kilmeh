"""Grade rtl-bidi-data-cells. Usage: python3 -I verify.py APP OUT

Prints one boolean per check as JSON and exits 0 only if every check passes. Known tokens of
each technical value must read left to right on screen, the table stays right to left, and the
Arabic words that open each value cell stay on the value's right.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # -I drops the script dir

from rtl_checks import (  # noqa: E402
    computed_direction,
    grade,
    root_dir_lang,
    testid_texts,
    text_kept,
    visual_order,
)

# the fixture's index.html, byte for byte (pinned by tests/test_rtl_vendoring.py): the graded
# text, which may gain only invisible direction marks
PRISTINE = testid_texts((HERE / "pristine_index.html").read_text(encoding="utf-8"))
ROWS = ["r-path", "r-version", "r-phone", "r-code"]

# (row, value testid, tokens of the value in typed order)
VALUES = [
    ("path", "path", ["/", "var", "error.log"]),
    ("version", "version", ["2.4.1", "build", "77"]),
    ("phone", "phone", ["962", "79", "123", "4567"]),
    ("code", "fn", ["getUser", "("]),
]

_LEAD_JS = """([cell, value]) => {
  const td = document.querySelector(cell), v = document.querySelector(value);
  if (!td || !v) return null;
  const walker = document.createTreeWalker(td, NodeFilter.SHOW_TEXT);
  let lead = walker.nextNode();
  while (lead && !lead.nodeValue.trim()) lead = walker.nextNode();
  if (!lead || v.contains(lead)) return null;
  const range = document.createRange();
  range.selectNodeContents(lead);
  const a = range.getBoundingClientRect(), b = v.getBoundingClientRect();
  // the same reversed-letter guard as visual_order: in the first Arabic word of the opening
  // text, the first letter must sit right of the last (bidi-override would flip them)
  const word = /[\\u0621-\\u064a]{2,}/.exec(lead.nodeValue);
  if (!word) return null;
  const mid = (j) => {
    const c = document.createRange();
    c.setStart(lead, j); c.setEnd(lead, j + 1);
    const r = c.getBoundingClientRect();
    return r.left + r.width / 2;
  };
  const reversed = !(mid(word.index) > mid(word.index + word[0].length - 1));
  return [a.left, b.right, reversed];
}"""


def arabic_lead_right(page, rows: list[tuple[str, str]]):
    """In each cell, the opening (Arabic) text sits right of the value element, with its
    letters in right-to-left order."""
    for cell, value in rows:
        got = page.evaluate(_LEAD_JS, [cell, value])
        if got is None:
            return False, f"{cell}: no opening Arabic text before {value}"
        lead_left, value_right, reversed_letters = got
        if reversed_letters:
            return False, f"{cell}: opening text has its letters reversed"
        if lead_left < value_right - 1:
            return False, f"{cell}: opening text left={lead_left:.0f} < value right={value_right:.0f}"
    return True, ""


PLAN = [
    (
        {"width": 1280},
        [
            ("root_dir_lang", root_dir_lang, {}),
            ("cells_rtl", computed_direction, {"selectors": ["table", "th", "td.label", "td.value"]}),
            ("text_kept", text_kept, {"expected": {r: PRISTINE[r] for r in ROWS}}),
        ]
        + [
            (
                f"order_{row}",
                visual_order,
                {"selector": f'[data-testid="{testid}"]', "tokens": tokens, "want": "ltr"},
            )
            for row, testid, tokens in VALUES
        ]
        + [
            (
                "arabic_lead_right",
                arabic_lead_right,
                {
                    "rows": [
                        (f'[data-testid="r-{row}"] td.value', f'[data-testid="{testid}"]')
                        for row, testid, _ in VALUES
                    ]
                },
            ),
        ],
    ),
]

if __name__ == "__main__":
    results = grade(Path(sys.argv[1]), PLAN)
    print(json.dumps(results, sort_keys=True))
    sys.exit(0 if all(results.values()) else 1)
