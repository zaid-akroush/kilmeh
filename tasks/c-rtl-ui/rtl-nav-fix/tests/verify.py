"""Grade rtl-nav-fix. Usage: python3 -I verify.py APP OUT

Prints one boolean per check as JSON and exits 0 only if every check passes. The page is
served to headless Chromium from APP; nothing is trusted from the agent's side but the files.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir

from rtl_checks import (  # noqa: E402
    computed_direction,
    grade,
    mirror_on_dir_flip,
    no_horizontal_overflow,
    no_physical_css,
    on_side,
    order_rtl,
    root_dir_lang,
)

LOGO = '[data-testid="logo"]'
SIGNIN = '[data-testid="signin"]'
TITLE = '[data-testid="hero-title"]'

PLAN = [
    (
        {"width": 1280},
        [
            ("root_dir_lang", root_dir_lang, {}),
            ("computed_direction", computed_direction, {"selectors": ["body", "footer"]}),
            ("on_side_logo", on_side, {"selector": LOGO, "side": "right"}),
            ("on_side_signin", on_side, {"selector": SIGNIN, "side": "left"}),
            ("order_rtl_nav", order_rtl, {"selector": '[data-testid="nav-link"]'}),
            (
                "mirror_on_dir_flip",
                mirror_on_dir_flip,
                {"selectors": [LOGO, "nav", SIGNIN, TITLE]},
            ),
            ("no_physical_css", no_physical_css, {}),
        ],
    ),
    ({"width": 360}, [("no_horizontal_overflow_360", no_horizontal_overflow, {})]),
]

if __name__ == "__main__":
    results = grade(Path(sys.argv[1]), PLAN)
    print(json.dumps(results, sort_keys=True))
    sys.exit(0 if all(results.values()) else 1)
