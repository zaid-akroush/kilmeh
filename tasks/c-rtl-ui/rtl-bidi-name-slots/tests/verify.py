"""Grade rtl-bidi-name-slots. Usage: python3 -I verify.py APP OUT

Prints one boolean per check as JSON and exits 0 only if every check passes. Every slot must be
isolated (computed style or Unicode controls), and known tokens around the Latin slots must land
where an isolated value puts them on screen.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # -I drops the script dir

from rtl_checks import (  # noqa: E402
    bidi_isolated,
    grade,
    root_dir_lang,
    testid_texts,
    text_kept,
    visual_order,
)

# the fixture's index.html, byte for byte (pinned by tests/test_rtl_vendoring.py): the graded
# text, which may gain only invisible direction marks
RAW = (HERE / "pristine_index.html").read_text(encoding="utf-8")
PRISTINE = testid_texts(RAW)
NOTES = ["n1", "n2", "n3", "n4"]
# n4's first two words (the verb and the Arabic name), taken from the pristine html, not retyped
N4_WORDS = re.sub(r"<[^>]+>", "", re.search(r'data-testid="n4">(.*?)</li>', RAW)[1]).split()[:2]

SLOTS = [f'[data-testid="{slot}"]' for slot in ("u1", "p1", "o1", "u2")]


def order(note: str, tokens: list[str], want: str) -> dict:
    return {"selector": f'[data-testid="{note}"]', "tokens": tokens, "want": want}


PLAN = [
    (
        {"width": 1280},
        [
            ("root_dir_lang", root_dir_lang, {}),
            ("bidi_isolated", bidi_isolated, {"selectors": SLOTS}),
            # the count after the name stays on the name's left in the Arabic sentence
            ("order_n1", visual_order, order("n1", ["Ahmad", "3"], "rtl")),
            # "++" stays at the end of the product name, on its right
            ("order_n2", visual_order, order("n2", ["Notes", "++"], "ltr")),
            # "#" stays in front of the order number, on its left
            ("order_n3", visual_order, order("n3", ["#", "A"], "ltr")),
            # the Arabic name keeps its right-to-left letter order
            ("order_n4", visual_order, order("n4", N4_WORDS, "rtl")),
            ("text_kept", text_kept, {"expected": {n: PRISTINE[n] for n in NOTES}}),
        ],
    ),
]

if __name__ == "__main__":
    results = grade(Path(sys.argv[1]), PLAN)
    print(json.dumps(results, sort_keys=True))
    sys.exit(0 if all(results.values()) else 1)
