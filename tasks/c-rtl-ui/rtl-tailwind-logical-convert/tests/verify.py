"""Grade rtl-tailwind-logical-convert. Usage: python3 -I verify.py APP OUT

APP is the agent's project, OUT the directory build.sh wrote `app.css` and `pristine.css` to. Each
page is served from APP, but `/dist/app.css` is replaced by OUT/app.css, so a hand-edited `dist/`
is never graded. The untouched fixture (tests/pristine, built into OUT/pristine.css) is rendered
at grade time for the expected left-to-right boxes and testid text, so no position is hard-coded.
Prints one boolean per check as JSON (keys `<page>.<check>`) and exits 0 only if every check passes.
"""

import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir

from rtl_checks import (  # noqa: E402
    ORIGIN,
    computed_direction,
    grade,
    no_horizontal_overflow,
    no_physical_css,
    no_physical_tailwind,
    root_dir_lang,
)

PRISTINE = Path(__file__).resolve().parent / "pristine"
TOL = 2.0  # px


def _t(name):
    return f'[data-testid="{name}"]'


# page -> its left-to-right islands
PAGES = {
    "index": [_t("email")],
    "notifications": [_t("webhook")],
    "billing": [_t("iban"), _t("card-number")],
}

_VISIBLE_JS = """
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

# Physical longhands compared by ltr_styles_unchanged, per element (`text-align` is resolved to
# left/right separately). Margins and inset are not here: they are graded through the boxes in
# ltr_layout_unchanged, so a different technique with the same geometry (gap for a margin, flex
# for a float) stays correct.
SIDES = ("top", "right", "bottom", "left")
STYLE_PROPS = [
    *[f"padding-{s}" for s in SIDES],
    *[f"border-{s}-width" for s in SIDES],
    *[f"border-{c}-radius" for c in ("top-left", "top-right", "bottom-right", "bottom-left")],
    *[f"scroll-padding-{s}" for s in SIDES],
]

# Two parts: every [data-testid] element in document order (id, box, text, visibility), and
# <body> plus every element under it, keyed by its tag/nth-of-type path from <body> (box,
# STYLE_PROPS, border colours, resolved text-align, and whether it has a class attribute).
_SNAPSHOT_JS = (
    "(props) => {"
    + f"const ISLANDS = {json.dumps(', '.join(s for sel in PAGES.values() for s in sel))};"
    + _VISIBLE_JS
    + """
  const testids = [...document.querySelectorAll('[data-testid]')].map(el => {
    const r = el.getBoundingClientRect();
    return {id: el.getAttribute('data-testid'), left: r.left, top: r.top, width: r.width,
            text: el.textContent.replace(/\\s+/g, ' ').trim(), visible: visible(el)};
  });
  const path = (el) => {
    const parts = [];
    for (let e = el; e && e !== document.body; e = e.parentElement) {
      let i = 0;
      for (let s = e.previousElementSibling; s; s = s.previousElementSibling) {
        if (s.tagName === e.tagName) i++;
      }
      parts.unshift(`${e.tagName.toLowerCase()}[${i}]`);
    }
    return parts.join('>') || 'body';
  };
  const styled = {};
  for (const el of [document.body, ...document.body.querySelectorAll('*')]) {
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    const style = {};
    for (const p of props) style[p] = cs.getPropertyValue(p);
    for (const s of ['top', 'right', 'bottom', 'left']) {
      style[`border-${s}-color`] = cs.getPropertyValue(`border-${s}-color`);
    }
    let ta = cs.textAlign.replace(/^-webkit-/, '');
    if (ta === 'start') ta = cs.direction === 'rtl' ? 'right' : 'left';
    if (ta === 'end') ta = cs.direction === 'rtl' ? 'left' : 'right';
    style['text-align'] = ta;
    // only the task's own islands count, and only as text-only leaves: an island testid on a
    // wrapper (body, main) is graded like any element
    const island = el.matches(ISLANDS) && el.childElementCount === 0;
    styled[path(el)] = {left: r.left, top: r.top, width: r.width, height: r.height, style,
                       cls: el.hasAttribute('class'), island, dir: cs.direction};
  }
  return {testids, styled, width: document.documentElement.clientWidth};
}"""
)

_LTR_SNAPSHOT_JS = (
    """async (props) => {
  const root = document.documentElement;
  const original = root.getAttribute('dir');
  const frames = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  try {
    root.setAttribute('dir', 'ltr');
    await frames();
    return ("""
    + _SNAPSHOT_JS
    + """)(props);
  } finally {
    if (original === null) root.removeAttribute('dir'); else root.setAttribute('dir', original);
    await frames();
  }
}"""
)

_cache: dict = {}


def pristine_snapshot(page, name: str, css: Path) -> dict:
    """Snapshot of the untouched fixture page, with the agent's <html lang> and dir="ltr".

    Rendered in a second page of the same browser context; page routes win over the context's,
    so the HTML and /dist/app.css come from the pristine copy and its build.
    """
    lang = page.evaluate("document.documentElement.getAttribute('lang') || ''")
    key = (name, lang)
    if key not in _cache:
        source = (PRISTINE / f"{name}.html").read_text("utf-8")
        assert source.count('<html lang="en">') == 1, "pristine fixture changed"
        body = source.replace(
            '<html lang="en">', f'<html lang="{html.escape(lang, quote=True)}" dir="ltr">'
        )
        other = page.context.new_page()
        try:
            other.route(
                f"{ORIGIN}/__pristine__/{name}.html",
                lambda r: r.fulfill(body=body, content_type="text/html; charset=utf-8"),
            )
            other.route(
                f"{ORIGIN}/dist/app.css",
                lambda r: r.fulfill(body=css.read_bytes(), content_type="text/css; charset=utf-8"),
            )
            other.goto(f"{ORIGIN}/__pristine__/{name}.html", wait_until="load")
            other.evaluate("document.fonts.ready.then(() => true)")
            _cache[key] = other.evaluate(_SNAPSHOT_JS, STYLE_PROPS)
        finally:
            other.close()
    return _cache[key]


def _by_id(items: list) -> dict:
    out: dict = {}
    for item in items:
        out.setdefault(item["id"], []).append(item)
    return out


def testids_and_text_kept(page, name: str, css: Path):
    """Every fixture data-testid is still there, visible, and the testid text is unchanged."""
    want = pristine_snapshot(page, name, css)["testids"]
    got = page.evaluate(_SNAPSHOT_JS, STYLE_PROPS)["testids"]
    have, need = _by_id(got), _by_id(want)
    for testid, items in need.items():
        if len(have.get(testid, [])) < len(items):
            return False, f"data-testid={testid}: {len(have.get(testid, []))} of {len(items)}"
    hidden = sorted({g["id"] for g in got if not g["visible"]})
    if hidden:
        return False, "not visible: " + " ".join(hidden)
    if [g["text"] for g in got] != [w["text"] for w in want]:
        return False, "the text of the data-testid elements changed"
    return True, ""


def ltr_layout_unchanged(page, name: str, css: Path):
    """With <html dir="ltr">, boxes keep the fixture's geometry (2 px).

    Each testid box keeps its left, top and width (per testid and occurrence), and each element
    that has a class in the fixture keeps its left, top, width and height (matched by its
    tag/nth-of-type path; this is where margins and inset are graded). The page's structure must
    stay: a fixture path missing from the page (an element added, removed, reordered or re-tagged
    before it) fails. Expected values are never printed.
    """
    want = pristine_snapshot(page, name, css)
    have = page.evaluate(_LTR_SNAPSHOT_JS, STYLE_PROPS)
    ids = _by_id(have["testids"])
    for testid, items in _by_id(want["testids"]).items():
        for i, (w, g) in enumerate(zip(items, ids.get(testid, []), strict=False)):
            for prop in ("left", "top", "width"):
                if abs(w[prop] - g[prop]) > TOL:
                    return False, f"{testid}[{i}] {prop} moved in ltr (now {g[prop]:.0f})"
    for path, w in want["styled"].items():
        if not w["cls"]:
            continue
        g = have["styled"].get(path)
        if g is None:
            return False, f"{path} is gone: elements were added, removed, reordered or re-tagged"
        for prop in ("left", "top", "width", "height"):
            if abs(w[prop] - g[prop]) > TOL:
                return False, f"{path} {prop} moved in ltr (now {g[prop]:.0f})"
    return True, ""


def ltr_styles_unchanged(page, name: str, css: Path):
    """With <html dir="ltr">, each element that has a class in the fixture keeps its padding,
    border widths, border colours (on sides with a border), corner radii, scroll-padding and
    text-align (start/end resolved to left/right), per physical side, matched by path (a missing
    path fails, as in ltr_layout_unchanged; the page side is snapshotted over every element, so an
    element whose class was removed still matches).

    Catches a conversion that drops or misplaces a utility without moving a box. Hover and other
    state-only styles are not seen. Expected values are never printed.
    """
    want = pristine_snapshot(page, name, css)["styled"]
    have = page.evaluate(_LTR_SNAPSHOT_JS, STYLE_PROPS)["styled"]
    for path, w in want.items():
        if not w["cls"]:
            continue
        g = have.get(path)
        if g is None:
            return False, f"{path} is gone: elements were added, removed, reordered or re-tagged"
        ws, gs = w["style"], g["style"]
        props = [*STYLE_PROPS, "text-align"]
        for side in SIDES:
            if ws[f"border-{side}-width"] != "0px" or gs[f"border-{side}-width"] != "0px":
                props.append(f"border-{side}-color")
        for prop in props:
            if ws[prop] != gs[prop]:
                return False, f"{path} {prop} changed in ltr (now {gs[prop]})"
    return True, ""


_BOTH_DIRS_JS = (
    """async (props) => {
  const root = document.documentElement;
  const original = root.getAttribute('dir');
  const frames = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const snap = ("""
    + _SNAPSHOT_JS
    + """);
  try {
    root.setAttribute('dir', 'rtl');
    await frames();
    const rtl = snap(props);
    root.setAttribute('dir', 'ltr');
    await frames();
    const ltr = snap(props);
    return {rtl, ltr};
  } finally {
    if (original === null) root.removeAttribute('dir'); else root.setAttribute('dir', original);
    await frames();
  }
}"""
)


def _swap(text: str) -> str:
    """Swap the words left and right (property names and text-align values)."""
    return re.sub(r"left|right", lambda m: "right" if m[0] == "left" else "left", text)


def rtl_mirrors_ltr(page):
    """The page mirrors exactly when only <html dir> flips: compared on the agent's own page, so
    no fixture value is involved.

    For every element under <body>, the RTL box is the LTR box mirrored about the viewport
    (left_rtl = W - left_ltr - width, same top, width and height, 2 px), and its padding, border
    widths, border colours (on sides with a border), corner radii and scroll-padding are the LTR
    values with left and right swapped; text-align (start/end resolved) swaps too. Left-to-right
    islands (the PAGES islands, only as text-only leaves) only mirror their position. Every
    other element's computed direction follows <html dir>, so a wrapper forced left-to-right (a
    dir attribute, dir=auto or CSS direction) fails.
    Elements with an empty box in both directions (display: none) are skipped.
    """
    got = page.evaluate(_BOTH_DIRS_JS, STYLE_PROPS)
    rtl, ltr, width = got["rtl"]["styled"], got["ltr"]["styled"], got["ltr"]["width"]
    for path, a in rtl.items():
        b = ltr.get(path)
        if b is None:
            continue
        if not (a["width"] or a["height"] or b["width"] or b["height"]):
            continue
        mirrored = width - b["left"] - b["width"]
        if abs(a["left"] - mirrored) > TOL or any(
            abs(a[k] - b[k]) > TOL for k in ("top", "width", "height")
        ):
            return False, (
                f"{path} not mirrored: rtl left={a['left']:.0f} w={a['width']:.0f}, "
                f"ltr left={b['left']:.0f} w={b['width']:.0f}, W={width:.0f}"
            )
        if a["island"]:
            continue
        if (a["dir"], b["dir"]) != ("rtl", "ltr"):
            return False, f"{path} direction is {a['dir']} in rtl, {b['dir']} in ltr"
        sa, sb = a["style"], b["style"]
        props = [*STYLE_PROPS, "text-align"]
        for side in SIDES:
            if sa[f"border-{side}-width"] != "0px" or sb[f"border-{_swap(side)}-width"] != "0px":
                props.append(f"border-{side}-color")
        for prop in props:
            want = _swap(sb["text-align"]) if prop == "text-align" else sb[_swap(prop)]
            if sa[prop] != want:
                return False, f"{path} {prop} is {sa[prop]} in rtl, {want} mirrored from ltr"
    return True, ""


_TEXT_START_JS = """(selectors) => selectors.map(s => {
  const el = document.querySelector(s);
  if (!el) return null;
  const cs = getComputedStyle(el), r = el.getBoundingClientRect();
  const range = document.createRange();
  range.selectNodeContents(el);
  const rects = [...range.getClientRects()].filter(x => x.width > 0);
  if (!rects.length) return {empty: true};
  return {text: Math.min(...rects.map(x => x.left)),
          edge: r.left + parseFloat(cs.borderLeftWidth) + parseFloat(cs.paddingLeft)};
})"""


def ltr_islands_kept(page, selectors: list):
    """In the Arabic page, each left-to-right island's text starts at its left content edge."""
    got = page.evaluate(_TEXT_START_JS, selectors)
    for selector, item in zip(selectors, got, strict=True):
        if item is None:
            return False, f"missing: {selector}"
        if item.get("empty"):
            return False, f"{selector} has no text"
        if abs(item["text"] - item["edge"]) > TOL:
            return False, (
                f"{selector} text starts at x={item['text']:.0f}, left edge {item['edge']:.0f}"
            )
    return True, ""


# Code can set dir and lang or restyle the page and then remove itself, so the source file is
# scanned too (parsed, not pattern-matched), as in rtl-contact-page-build's static_page.
BANNED_TAGS = {
    "script",
    "iframe",
    "frame",
    "frameset",
    "object",
    "embed",
    "applet",
    "template",
    "base",
}


class _Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.problems = []

    def _look(self, tag, attrs):
        if tag in BANNED_TAGS:
            self.problems.append(f"<{tag}>")
        for name, value in attrs:
            if name.lower().startswith("on"):
                self.problems.append(f"<{tag} {name}>")
            # browsers drop whitespace and control characters inside a URL scheme
            if re.sub(r"[\x00-\x20]+", "", value or "").lower().startswith("javascript:"):
                self.problems.append(f"<{tag} {name}=javascript:>")

    def handle_starttag(self, tag, attrs):
        self._look(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self._look(tag, attrs)


_STYLES_JS = """(banned) => ({
  links: [...document.querySelectorAll('link[rel~="stylesheet"]')]
    .map(l => new URL(l.getAttribute('href'), document.baseURI).pathname),
  styleElements: document.querySelectorAll('style:not([data-kilmeh])').length,
  styleAttributes: document.querySelectorAll('[style]').length,
  code: [...document.querySelectorAll('*')].flatMap(el => [
    ...(banned.includes(el.tagName.toLowerCase()) ? [el.tagName.toLowerCase()] : []),
    ...[...el.attributes].filter(a => a.name.toLowerCase().startsWith('on'))
      .map(a => `${el.tagName.toLowerCase()}[${a.name}]`),
  ]),
})"""


def css_from_build(page, source: Path):
    """All styling comes from the rebuilt dist/app.css and nothing runs code.

    No other stylesheet, <style> or style="". The page's source file has no <script>, frame,
    plugin, template or base element, no on* handler and no javascript: URL (a script that
    removes itself is still in the file), and none of those exist at runtime either.
    """
    try:
        scan = _Scan()
        scan.feed(source.read_text(encoding="utf-8", errors="replace"))
        scan.close()
    except OSError as exc:
        return False, f"cannot read {source.name}: {exc}"
    if scan.problems:
        return False, f"{source.name}: {scan.problems[0]} is not allowed"
    got = page.evaluate(_STYLES_JS, sorted(BANNED_TAGS))
    if got["links"] != ["/dist/app.css"]:
        return False, f"stylesheets must be only /dist/app.css, got {got['links']}"
    if got["styleElements"] or got["styleAttributes"] or got["code"]:
        return False, (
            f"<style>: {got['styleElements']}, style attributes: {got['styleAttributes']}, "
            f"code: {', '.join(sorted(set(got['code']))) or 'none'}"
        )
    return True, ""


def make_plan(app: Path, out: Path) -> list:
    overrides = {"/dist/app.css": out / "app.css"}
    css = out / "pristine.css"
    plan = []
    for name, islands in PAGES.items():
        path = f"/{name}.html"
        plan.append(
            (
                {"path": path, "width": 1280, "overrides": overrides},
                [
                    (f"{name}.root_dir_lang", root_dir_lang, {}),
                    (
                        f"{name}.islands_direction",
                        computed_direction,
                        {"selectors": islands, "want": "ltr"},
                    ),
                    (f"{name}.ltr_islands_kept", ltr_islands_kept, {"selectors": islands}),
                    (f"{name}.rtl_mirrors_ltr", rtl_mirrors_ltr, {}),
                    (f"{name}.no_physical_tailwind", no_physical_tailwind, {}),
                    (
                        f"{name}.testids_and_text_kept",
                        testids_and_text_kept,
                        {"name": name, "css": css},
                    ),
                    (
                        f"{name}.ltr_layout_unchanged",
                        ltr_layout_unchanged,
                        {"name": name, "css": css},
                    ),
                    (
                        f"{name}.ltr_styles_unchanged",
                        ltr_styles_unchanged,
                        {"name": name, "css": css},
                    ),
                    (f"{name}.css_from_build", css_from_build, {"source": app / f"{name}.html"}),
                    (f"{name}.no_physical_css", no_physical_css, {}),
                ],
            )
        )
        plan.append(
            (
                {"path": path, "width": 360, "overrides": overrides},
                [(f"{name}.no_horizontal_overflow_360", no_horizontal_overflow, {})],
            )
        )
    return plan


if __name__ == "__main__":
    app = Path(sys.argv[1])
    results = grade(app, make_plan(app, Path(sys.argv[2])))
    print(json.dumps(results, sort_keys=True))
    sys.exit(0 if all(results.values()) else 1)
