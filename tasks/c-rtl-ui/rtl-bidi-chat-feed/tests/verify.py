"""Grade rtl-bidi-chat-feed. Usage: python3 -I verify.py APP OUT

Prints one boolean per check as JSON and exits 0 only if every check passes. Each message is
graded by where known Latin and number tokens land on screen: in a message with a right-to-left
base they read right to left, in one with a left-to-right base they read left to right. Two
words of one Arabic run in each message must also read right to left (`arabic_words.json`,
copied from the fixture's bytes, never retyped), and no token may have its letters reversed.
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

ARABIC = json.loads((HERE / "arabic_words.json").read_text(encoding="utf-8"))

# (message, tokens in typed order, base direction from the first strong letter)
MESSAGES = [
    ("m1", ["Ahmad", "5"], "rtl"),  # Arabic first
    ("m2", ["Hello", "Thanks"], "ltr"),  # English first
    ("m3", ["https", "3"], "ltr"),  # link first
    ("m4", ["Sara", "Omar"], "rtl"),  # Arabic first, two Latin names
    ("m5", ["0791234567", "Ali"], "rtl"),  # Arabic first, phone number
]



def message_order(page, selector: str, tokens: list[str], want: str, arabic: list[str]):
    """Latin and number tokens read in the base direction; the Arabic words read right to left."""
    ok, detail = visual_order(page, selector, tokens, want)
    if not ok:
        return ok, detail
    return visual_order(page, selector, arabic, "rtl")


PLAN = [
    (
        {"width": 1280},
        [
            ("root_dir_lang", root_dir_lang, {}),
            ("feed_rtl", computed_direction, {"selectors": ["body", '[data-testid="feed"]']}),
            ("text_kept", text_kept, {"expected": {m: PRISTINE[m] for m, _, _ in MESSAGES}}),
        ]
        + [
            (
                f"order_{msg}",
                message_order,
                {
                    "selector": f'[data-testid="{msg}"] .text',
                    "tokens": tokens,
                    "want": want,
                    "arabic": ARABIC[msg],
                },
            )
            for msg, tokens, want in MESSAGES
        ],
    ),
]

if __name__ == "__main__":
    results = grade(Path(sys.argv[1]), PLAN)
    print(json.dumps(results, sort_keys=True))
    sys.exit(0 if all(results.values()) else 1)
