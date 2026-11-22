"""Grade rtl-order-summary-fix. Usage: python3 -I verify.py APP OUT

Prints one boolean per check as JSON and exits 0 only if every check passes. The Arabic name
typed into the name field is `name_sample.txt`, copied from the fixture's bytes (never retyped).
"""

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # -I drops the script dir

from rtl_checks import (  # noqa: E402
    bidi_isolated,
    fits_width,
    grade,
    icon_points,
    input_direction,
    no_horizontal_overflow,
    root_dir_lang,
)

NAME_AR = (HERE / "name_sample.txt").read_text(encoding="utf-8")
HEAD = "[data-part=head]"
RUNS = [f'[data-testid="{run}"]' for run in ("inv", "phone", "user", "price")]


ICONS = ["logo-icon", "play-icon", "back-icon", "next-icon"]
# Digest of each icon's whitespace-normalised markup, as the browser serialises it, taken from
# the original fixture. Flipping must be done with CSS, so the SVG markup has to stay as shipped.
ICON_MARKUP_DIGEST = {
    "logo-icon": "9469a2fb8a5a8705ce9ef50a19739f8ac6dfe13c9368cd866c9abfee5301b923",
    "play-icon": "83b7869c5df0fb75a8740fa1db0ba65efeaa9ba1abde6913ad96e6c031ffb3ab",
    "back-icon": "945dcfa6315efacff30c1958d26600776a5532361d8d6d25219d2eefc4ae50a7",
    "next-icon": "7f107880f0c47b10c6cc106170b4ed63e561dc89e3c4ded5a5277719f3dc5dc8",
}


def icon_markup_digests(page) -> dict:
    html = page.evaluate(
        "(ids) => ids.map(id => {"
        ' const el = document.querySelector(`[data-testid="${id}"]`);'
        " return el ? el.outerHTML : null; })",
        ICONS,
    )
    out = {}
    for icon_id, markup in zip(ICONS, html, strict=True):
        if markup is not None:
            norm = re.sub(r"\s+", " ", markup).replace("> <", "><").strip()
            out[icon_id] = hashlib.sha256(norm.encode("utf-8")).hexdigest()
    return out


def svg_markup_unchanged(page):
    got = icon_markup_digests(page)
    for icon_id, want in ICON_MARKUP_DIGEST.items():
        if got.get(icon_id) != want:
            return False, f"{icon_id}: markup changed or missing; flip it with CSS instead"
    return True, ""


def icon(testid: str, want: str) -> dict:
    return {"icon": f'[data-testid="{testid}"]', "head": HEAD, "want": want}


PLAN = [
    (
        {"width": 360},
        [
            ("root_dir_lang", root_dir_lang, {}),
            ("icon_next", icon_points, icon("next-icon", "left")),
            ("icon_back", icon_points, icon("back-icon", "right")),
            ("icon_logo", icon_points, icon("logo-icon", "right")),
            ("icon_play", icon_points, icon("play-icon", "right")),
            ("bidi_isolated", bidi_isolated, {"selectors": RUNS}),
            (
                "input_email",
                input_direction,
                {"selector": '[data-testid="email"]', "text": "a@b.co", "want": "ltr"},
            ),
            (
                "input_phone",
                input_direction,
                {"selector": '[data-testid="phone-input"]', "text": "0791234567", "want": "ltr"},
            ),
            (
                "input_name_ar",
                input_direction,
                {"selector": '[data-testid="name"]', "text": NAME_AR, "want": "rtl"},
            ),
            (
                "input_name_latin",
                input_direction,
                {"selector": '[data-testid="name"]', "text": "Sara", "want": "ltr"},
            ),
            ("no_horizontal_overflow", no_horizontal_overflow, {}),
            ("table_fits", fits_width, {"selector": "table"}),
            ("svg_markup_unchanged", svg_markup_unchanged, {}),
        ],
    ),
]

if __name__ == "__main__":
    results = grade(Path(sys.argv[1]), PLAN)
    print(json.dumps(results, sort_keys=True))
    sys.exit(0 if all(results.values()) else 1)
