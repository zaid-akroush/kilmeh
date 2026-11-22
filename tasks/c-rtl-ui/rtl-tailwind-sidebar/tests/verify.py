"""Grade rtl-tailwind-sidebar. Usage: python3 -I verify.py APP OUT

APP is the agent's project, OUT the directory build.sh wrote `app.css` to. The page is served from
APP, but `/dist/app.css` is replaced by OUT/app.css, so a hand-edited `dist/` is never graded.
Prints one boolean per check as JSON and exits 0 only if every check passes.
"""

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir

from rtl_checks import (  # noqa: E402
    grade,
    mirror_on_dir_flip,
    no_horizontal_overflow,
    no_physical_css,
    no_physical_tailwind,
    on_side,
    root_dir_lang,
)

SIDEBAR = '[data-testid="sidebar"]'
MAIN = '[data-testid="main"]'
BADGE = '[data-testid="badge"]'

# data-testid -> how many elements the fixture has. Every one must stay, visible.
TESTIDS = {
    "sidebar": 1,
    "brand": 1,
    "side-nav": 1,
    "nav-link": 4,
    "main": 1,
    "page-title": 1,
    "card": 3,
    "badge": 1,
    "footer-note": 1,
}
# sha256 of the whitespace-collapsed textContent of every [data-testid] element, in document
# order, joined by newlines (taken from the original fixture): the Arabic text must stay.
TEXT_DIGEST = "9a0cacdba4c5ace4b5e33f76a46d88d29b1bb3a12f268d38223207c21044dcff"

SIDEBAR_MIN_WIDTH = 200  # the fixture's w-64 is 256px
MAIN_MIN_WIDTH = 300  # at the 1280px viewport

_JS_COMMON = """
const visible = (el) => {
  const r = el.getBoundingClientRect();
  if (!(r.width > 1 && r.height > 1)) return false;
  for (let e = el; e; e = e.parentElement) {
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || parseFloat(cs.opacity) === 0) return false;
    if (e === el && cs.visibility !== 'visible') return false;
  }
  return true;
};
"""

_BESIDE_JS = (
    "() => {"
    + _JS_COMMON
    + """
  const a = document.querySelector('[data-testid="sidebar"]');
  const m = document.querySelector('[data-testid="main"]');
  if (!a || !m) return null;
  const ra = a.getBoundingClientRect(), rm = m.getBoundingClientRect();
  return {aLeft: ra.left, aWidth: ra.width, mRight: rm.right, mWidth: rm.width,
          aVisible: visible(a), mVisible: visible(m)};
}"""
)


def main_beside_sidebar(page):
    """RTL: the main box lies entirely left of the sidebar, and neither is hidden or shrunk."""
    got = page.evaluate(_BESIDE_JS)
    if got is None:
        return False, "missing sidebar or main"
    if not (got["aVisible"] and got["mVisible"]):
        return False, "sidebar or main is not visible"
    if got["aWidth"] < SIDEBAR_MIN_WIDTH or got["mWidth"] < MAIN_MIN_WIDTH:
        return False, f"sidebar {got['aWidth']:.0f}px or main {got['mWidth']:.0f}px too narrow"
    if got["mRight"] > got["aLeft"] + 1:
        return False, f"main right edge {got['mRight']:.0f} > sidebar left edge {got['aLeft']:.0f}"
    return True, ""


_TESTIDS_JS = (
    "(ids) => {"
    + _JS_COMMON
    + """
  const els = [...document.querySelectorAll('[data-testid]')];
  const counts = {}, hidden = [];
  for (const el of els) {
    const id = el.getAttribute('data-testid');
    counts[id] = (counts[id] || 0) + 1;
    if (!visible(el)) hidden.push(id);
  }
  const texts = els.map(el => el.textContent.replace(/\\s+/g, ' ').trim());
  return {counts, hidden, text: texts.join('\\n')};
}"""
)


def testids_kept(page):
    """Every fixture data-testid is still there, visible, with the original text."""
    got = page.evaluate(_TESTIDS_JS, list(TESTIDS))
    for testid, count in TESTIDS.items():
        if got["counts"].get(testid, 0) < count:
            return False, f"data-testid={testid}: {got['counts'].get(testid, 0)} of {count}"
    if got["hidden"]:
        return False, "not visible: " + " ".join(sorted(set(got["hidden"])))
    if hashlib.sha256(got["text"].encode("utf-8")).hexdigest() != TEXT_DIGEST:
        return False, "the text of the data-testid elements changed"
    return True, ""


_STYLES_JS = """() => ({
  links: [...document.querySelectorAll('link[rel~="stylesheet"]')]
    .map(l => new URL(l.getAttribute('href'), document.baseURI).pathname),
  styleElements: document.querySelectorAll('style:not([data-kilmeh])').length,
  styleAttributes: document.querySelectorAll('[style]').length,
  scripts: document.querySelectorAll('script').length,
})"""


def css_from_build(page):
    """All styling comes from the rebuilt dist/app.css: no other sheet, <style> or style=""."""
    got = page.evaluate(_STYLES_JS)
    if got["links"] != ["/dist/app.css"]:
        return False, f"stylesheets must be only /dist/app.css, got {got['links']}"
    if got["styleElements"] or got["styleAttributes"] or got["scripts"]:
        return False, (
            f"<style>: {got['styleElements']}, style attributes: {got['styleAttributes']}, "
            f"<script>: {got['scripts']}"
        )
    return True, ""


def make_plan(out: Path) -> list:
    overrides = {"/dist/app.css": out / "app.css"}
    return [
        (
            {"width": 1280, "overrides": overrides},
            [
                ("root_dir_lang", root_dir_lang, {}),
                ("on_side_aside", on_side, {"selector": SIDEBAR, "side": "right"}),
                ("main_beside_sidebar", main_beside_sidebar, {}),
                (
                    "mirror_on_dir_flip",
                    mirror_on_dir_flip,
                    {"selectors": [SIDEBAR, MAIN, BADGE]},
                ),
                ("no_physical_tailwind", no_physical_tailwind, {}),
                ("testids_kept", testids_kept, {}),
                ("css_from_build", css_from_build, {}),
                ("no_physical_css", no_physical_css, {}),
            ],
        ),
        (
            {"width": 360, "overrides": overrides},
            [("no_horizontal_overflow_360", no_horizontal_overflow, {})],
        ),
    ]


if __name__ == "__main__":
    results = grade(Path(sys.argv[1]), make_plan(Path(sys.argv[2])))
    print(json.dumps(results, sort_keys=True))
    sys.exit(0 if all(results.values()) else 1)
