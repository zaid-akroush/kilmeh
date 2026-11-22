"""Grade rtl-contact-page-build. Usage: python3 -I verify.py APP OUT

Prints one boolean per check as JSON and exits 0 only if every check passes.

Besides the library checks, four task-local checks keep the page honest: every required element
is visible, inside the viewport and not clipped by an ancestor (`elements_fit`); nothing is
shrunk with zoom or transform scale and text stays readable (`no_shrink_tricks`); the visible
text is Arabic (`arabic_text`); and the arrow SVG markup is the shipped markup, so the arrow has
to be flipped with CSS (`svg_markup_unchanged`). The Arabic name typed into the name field is
`name_sample.txt`, copied byte for byte from another task's fixture (never retyped).
"""

import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # -I drops the script dir

from rtl_checks import (  # noqa: E402
    bidi_isolated,
    computed_direction,
    grade,
    icon_points,
    input_direction,
    no_horizontal_overflow,
    no_physical_css,
    on_side,
    order_rtl,
    root_dir_lang,
)

NAME_AR = (HERE / "name_sample.txt").read_text(encoding="utf-8")


def tid(name: str) -> str:
    return f'[data-testid="{name}"]'


# data-testid -> exactly how many elements must match (decoys fail)
REQUIRED = {
    "page-header": 1,
    "logo": 1,
    "nav-link": 3,
    "contact-text": 1,
    "phone-text": 1,
    "email-text": 1,
    "contact-form": 1,
    "name": 1,
    "email-input": 1,
    "phone-input": 1,
    "next": 1,
    "next-icon": 1,
}
TEXT_IDS = ["logo", "nav-link", "contact-text", "name", "email-input", "phone-input", "next"]
ARABIC_IDS = ["logo", "nav-link", "next", "contact-text"]
MIN_FONT_PX = 12

# Digest of the arrow's whitespace-normalised markup as the browser serialises it.
NEXT_ICON_DIGEST = "7f107880f0c47b10c6cc106170b4ed63e561dc89e3c4ded5a5277719f3dc5dc8"

# Shared by elements_fit and arabic_text. An element is "seen" only if it has a box, is not
# display:none, visibility:hidden or (with its ancestors) 90 percent transparent, has a text
# colour that is not transparent, and, after scrolling it into view, the element at the centre of
# one of its boxes is the element itself or something inside it (so clip-path, overlays and
# covering elements fail). It must also start within the first 3 screens of the page.
_SEEN_JS = """
const canvas = document.createElement('canvas');
canvas.width = canvas.height = 1;
const ctx = canvas.getContext('2d', {willReadFrequently: true});
const rgba = (c) => {
  ctx.clearRect(0, 0, 1, 1);
  ctx.fillStyle = '#000';
  ctx.fillStyle = c;
  ctx.fillRect(0, 0, 1, 1);
  return [...ctx.getImageData(0, 0, 1, 1).data];
};
const alpha = (c) => rgba(c)[3] / 255;
const paintProblem = (el) => {
  const r = el.getBoundingClientRect();
  if (!(r.width > 0 && r.height > 0)) return 'has no size';
  let opacity = 1;
  for (let e = el; e; e = e.parentElement) {
    const cs = getComputedStyle(e);
    if (cs.display === 'none') return 'is display:none';
    opacity *= parseFloat(cs.opacity);
  }
  const cs = getComputedStyle(el);
  if (cs.visibility !== 'visible') return 'is visibility:hidden';
  if (opacity <= 0.1) return 'is transparent';
  if (alpha(cs.color) <= 0.5) return 'has a transparent text colour';
  return null;
};
const textInView = (node, parent) => {
  const range = document.createRange();
  range.selectNodeContents(node);
  for (const r of range.getClientRects()) {
    let box = {left: Math.max(r.left, 0), right: Math.min(r.right, innerWidth),
               top: Math.max(r.top, 0), bottom: Math.min(r.bottom, innerHeight)};
    for (let p = parent; p && p !== document.documentElement; p = p.parentElement) {
      const cs = getComputedStyle(p);
      if (cs.overflowX === 'visible' && cs.overflowY === 'visible') continue;
      const pr = p.getBoundingClientRect();
      box = {left: Math.max(box.left, pr.left), right: Math.min(box.right, pr.right),
             top: Math.max(box.top, pr.top), bottom: Math.min(box.bottom, pr.bottom)};
    }
    if (box.right - box.left > 1 && box.bottom - box.top > 1) return true;
  }
  return false;
};
const reached = (el, within) => {
  el.scrollIntoView({block: 'center', inline: 'nearest', behavior: 'instant'});
  for (const r of el.getClientRects()) {
    const left = Math.max(r.left, 0), right = Math.min(r.right, innerWidth);
    const top = Math.max(r.top, 0), bottom = Math.min(r.bottom, innerHeight);
    if (right <= left || bottom <= top) continue;
    const hit = document.elementFromPoint((left + right) / 2, (top + bottom) / 2);
    if (hit && within.contains(hit)) return true;
  }
  return false;
};
"""

_FIT_JS = (
    """(required) => {
  const W = document.documentElement.clientWidth;
  const sx = scrollX, sy = scrollY;
  """
    + _SEEN_JS
    + """
  const problems = [];
  for (const [id, count] of Object.entries(required)) {
    const els = [...document.querySelectorAll(`[data-testid="${id}"]`)];
    if (els.length !== count) {
      problems.push(`${id}: ${els.length} found, need exactly ${count}`);
      continue;
    }
    for (const el of els) {
      const bad = paintProblem(el);
      if (bad) { problems.push(`${id} ${bad}`); continue; }
      const r = el.getBoundingClientRect();
      if (r.left < -1 || r.right > W + 1) {
        problems.push(`${id} sticks out of the screen [${Math.round(r.left)}, ${Math.round(r.right)}]`);
        continue;
      }
      let clipped = null;
      for (let p = el.parentElement; p && p !== document.documentElement; p = p.parentElement) {
        if (getComputedStyle(p).overflowX === 'visible') continue;
        const pr = p.getBoundingClientRect();
        if (r.left < pr.left - 1 || r.right > pr.right + 1) { clipped = p.tagName.toLowerCase(); break; }
      }
      if (clipped) { problems.push(`${id} is clipped by <${clipped}>`); continue; }
      if (r.top + sy > 3 * innerHeight) { problems.push(`${id} starts below the first 3 screens`); continue; }
      if (!reached(el, el)) problems.push(`${id} is covered or clipped (nothing of it is hit at its centre)`);
    }
  }
  scrollTo(sx, sy);
  return problems;
}"""
)


def elements_fit(page):
    problems = page.evaluate(_FIT_JS, REQUIRED)
    return not problems, "; ".join(problems[:6])


_SHRINK_JS = """([textIds, minFont]) => {
  const problems = [];
  for (const el of document.querySelectorAll('html, body, body *')) {
    const cs = getComputedStyle(el);
    const tag = el.tagName.toLowerCase();
    if (cs.zoom && cs.zoom !== '1') problems.push(`<${tag}> zoom ${cs.zoom}`);
    if (cs.transform && cs.transform !== 'none') {
      const m = cs.transform.match(/matrix(3d)?\\(([^)]+)\\)/);
      const v = m ? m[2].split(',').map(Number) : null;
      const [a, b, c, d] = !v ? [0, 0, 0, 0] : m[1] ? [v[0], v[1], v[4], v[5]] : v;
      if (Math.abs(Math.hypot(a, b) - 1) > 0.01 || Math.abs(Math.hypot(c, d) - 1) > 0.01) {
        problems.push(`<${tag}> transform ${cs.transform}`);
      }
    }
    if (cs.scale && cs.scale !== 'none') {
      const parts = cs.scale.split(' ').map(Number);
      if (parts.some(n => Math.abs(Math.abs(n) - 1) > 0.01)) problems.push(`<${tag}> scale ${cs.scale}`);
    }
  }
  for (const id of textIds) {
    for (const el of document.querySelectorAll(`[data-testid="${id}"]`)) {
      const size = parseFloat(getComputedStyle(el).fontSize);
      if (size < minFont) problems.push(`${id} font-size ${size}px`);
    }
  }
  return problems;
}"""


def no_shrink_tricks(page):
    problems = page.evaluate(_SHRINK_JS, [TEXT_IDS, MIN_FONT_PX])
    return not problems, "; ".join(problems[:6])


ARABIC_RANGE = chr(0x0600) + "-" + chr(0x06FF)
_ARABIC_JS = (
    """(ids) => {
  const sx = scrollX, sy = scrollY;
  const arabic = new RegExp("[ARABIC_RANGE]");
  """
    + _SEEN_JS
    + """
  const results = [];
  for (const id of ids) {
    for (const el of document.querySelectorAll(`[data-testid="${id}"]`)) {
      let seen = false;
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      for (let n = walker.nextNode(); n && !seen; n = walker.nextNode()) {
        if (!arabic.test(n.nodeValue)) continue;
        const parent = n.parentElement;
        seen = !paintProblem(parent) && reached(parent, parent) && textInView(n, parent);
      }
      results.push([id, seen]);
    }
  }
  scrollTo(sx, sy);
  return results;
}"""
).replace("ARABIC_RANGE", ARABIC_RANGE)


def arabic_text(page):
    results = page.evaluate(_ARABIC_JS, ARABIC_IDS)
    if not results:
        return False, "no text found"
    for test_id, seen in results:
        if not seen:
            return False, f"{test_id} has no visible Arabic text"
    return True, ""


APP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
# Scripts, frames, plugins, templates and base can set dir, lang and the field directions from
# somewhere the checks do not look (a hidden iframe patching its parent, a script that removes
# itself, an onload handler). The HTML is parsed, not pattern-matched: comments are ignored and
# `<input/onfocus=...>` is found however the attribute is delimited.
BANNED_TAGS = {"script", "iframe", "frame", "frameset", "object", "embed", "applet", "template", "base"}


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


_RUNTIME_JS = """(banned) => {
  const bad = [];
  for (const el of document.querySelectorAll('*')) {
    const tag = el.tagName.toLowerCase();
    if (banned.includes(tag)) bad.push(tag);
    for (const a of el.attributes) {
      if (a.name.toLowerCase().startsWith('on')) bad.push(tag + '[' + a.name + ']');
    }
  }
  return bad;
}"""
MARKUP_SUFFIXES = {".html", ".htm", ".xhtml", ".svg", ".xml"}


def static_page(page):
    """The page is static HTML and CSS: nothing that can run code, in the files or at runtime.

    Every HTML, SVG and XML file in the app is parsed; any banned element, any attribute whose
    name starts with `on`, any `javascript:` URL or any JavaScript file fails. At runtime no
    element may carry an `on*` attribute or be a banned element, and exactly one frame loads.
    """
    for path in sorted(APP.rglob("*")):
        suffix = path.suffix.lower()
        if not path.is_file():
            continue
        if suffix in {".js", ".mjs"}:
            return False, f"{path.name}: JavaScript files are not allowed"
        if suffix in MARKUP_SUFFIXES:
            scan = _Scan()
            scan.feed(path.read_text(encoding="utf-8", errors="replace"))
            scan.close()
            if scan.problems:
                return False, f"{path.name}: {scan.problems[0]} is not allowed"
    live = page.evaluate(_RUNTIME_JS, sorted(BANNED_TAGS))
    if live:
        return False, f"found at runtime: {', '.join(sorted(set(live)))}"
    if len(page.frames) != 1:
        return False, f"{len(page.frames)} frames loaded, expected 1"
    return True, ""


CONTRAST_IDS = [
    "logo", "nav-link", "contact-text", "phone-text", "email-text",
    "name", "email-input", "phone-input", "next",
]  # fmt: skip
MIN_CONTRAST = 3.0

# An overlay is any element or ::before/::after with pointer-events:none, positioned fixed or
# absolute (itself or through an ancestor), with a background colour or image, whose box meets a
# graded element. elementFromPoint ignores pointer-events:none boxes, so they are checked here.
_OVERLAY_JS = (
    """(ids) => {
  """
    + _SEEN_JS
    + """
  const graded = ids.flatMap(id => [...document.querySelectorAll(`[data-testid="${id}"]`)]);
  const meets = (b) => b.right > b.left && b.bottom > b.top && graded.some(g => {
    const r = g.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && b.left < r.right && b.right > r.left
      && b.top < r.bottom && b.bottom > r.top;
  });
  const hasBg = (cs) => alpha(cs.backgroundColor) > 0 || cs.backgroundImage !== 'none';
  const floats = (cs) => cs.position === 'fixed' || cs.position === 'absolute';
  const inFloating = (el) => {
    for (let e = el; e; e = e.parentElement) if (floats(getComputedStyle(e))) return true;
    return false;
  };
  const related = (el) => graded.some(g => g.contains(el) || el.contains(g));
  const pseudoBox = (host, pcs) => {
    const w = parseFloat(pcs.width) || 0, h = parseFloat(pcs.height) || 0;
    const l = parseFloat(pcs.left), t = parseFloat(pcs.top);
    if (pcs.position === 'fixed') {
      return {left: l, top: t, right: l + w, bottom: t + h};
    }
    let cb = host;
    while (cb && getComputedStyle(cb).position === 'static') cb = cb.parentElement;
    const o = cb ? cb.getBoundingClientRect() : {left: -scrollX, top: -scrollY};
    const ox = o.left + (cb ? cb.clientLeft : 0), oy = o.top + (cb ? cb.clientTop : 0);
    if (isNaN(l) || isNaN(t)) {
      const hr = host.getBoundingClientRect();
      return {left: hr.left, top: hr.top, right: hr.left + w, bottom: hr.top + h};
    }
    return {left: ox + l, top: oy + t, right: ox + l + w, bottom: oy + t + h};
  };
  const problems = [];
  for (const el of document.querySelectorAll('html, body, body *')) {
    const tag = el.tagName.toLowerCase();
    const cs = getComputedStyle(el);
    if (!['html', 'body'].includes(tag) && !related(el) && cs.pointerEvents === 'none'
        && inFloating(el) && hasBg(cs) && meets(el.getBoundingClientRect())) {
      problems.push(`<${tag}> overlay (pointer-events:none, positioned, painted) over a listed element`);
    }
    for (const pseudo of ['::before', '::after']) {
      const pcs = getComputedStyle(el, pseudo);
      if (['none', 'normal'].includes(pcs.content) || !floats(pcs)) continue;
      if (pcs.pointerEvents === 'none' && hasBg(pcs) && meets(pseudoBox(el, pcs))) {
        problems.push(`<${tag}>${pseudo} overlay over a listed element`);
      }
    }
  }
  return problems;
}"""
)


def no_overlays(page):
    """No unclickable painted layer (fixed or absolute, pointer-events:none) sits over a listed
    element: `elementFromPoint` skips such layers, so they are checked directly."""
    problems = page.evaluate(_OVERLAY_JS, list(REQUIRED))
    return not problems, "; ".join(problems[:4])


_EFFECTS_JS = """(ids) => {
  const problems = [];
  for (const id of ids) {
    for (const el of document.querySelectorAll(`[data-testid="${id}"]`)) {
      for (let e = el; e; e = e.parentElement) {
        const cs = getComputedStyle(e);
        const tag = e.tagName.toLowerCase();
        if (cs.filter !== 'none') problems.push(`${id}: <${tag}> has filter ${cs.filter}`);
        if (cs.backdropFilter && cs.backdropFilter !== 'none') {
          problems.push(`${id}: <${tag}> has backdrop-filter`);
        }
        if (cs.mixBlendMode !== 'normal') problems.push(`${id}: <${tag}> has mix-blend-mode`);
      }
    }
  }
  return problems;
}"""


def no_effects(page):
    """No filter, backdrop-filter or mix-blend-mode on a listed element or any of its ancestors."""
    problems = page.evaluate(_EFFECTS_JS, list(REQUIRED))
    return not problems, "; ".join(problems[:4])


_CONTRAST_JS = (
    """([ids, minRatio]) => {
  """
    + _SEEN_JS
    + """
  const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
  const lum = ([r, g, b]) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
  const over = (top, base) => {
    const a = top[3] / 255;
    return [0, 1, 2].map(i => top[i] * a + base[i] * (1 - a)).concat([255]);
  };
  const problems = [];
  for (const id of ids) {
    for (const el of document.querySelectorAll(`[data-testid="${id}"]`)) {
      const chain = [];
      for (let e = el; e; e = e.parentElement) chain.unshift(rgba(getComputedStyle(e).backgroundColor));
      let bg = [255, 255, 255, 255];
      for (const layer of chain) if (layer[3] > 0) bg = over(layer, bg);
      const fg = over(rgba(getComputedStyle(el).color), bg);
      const [hi, lo] = [lum(fg), lum(bg)].sort((x, y) => y - x);
      const ratio = (hi + 0.05) / (lo + 0.05);
      if (ratio < minRatio) problems.push(`${id} contrast ${ratio.toFixed(2)}:1`);
    }
  }
  return problems;
}"""
)


def readable_contrast(page):
    """Text and form controls have a WCAG contrast of at least 3:1 against their background.

    The background is the first non-transparent background colour up the ancestors (white by
    default, semi-transparent layers composited); background images are not evaluated.
    """
    problems = page.evaluate(_CONTRAST_JS, [CONTRAST_IDS, MIN_CONTRAST])
    return not problems, "; ".join(problems[:4])



def svg_markup_unchanged(page):
    markup = page.evaluate(
        "() => { const el = document.querySelector('[data-testid=\"next-icon\"]');"
        " return el ? el.outerHTML : null; }"
    )
    if markup is None:
        return False, "next-icon missing"
    norm = re.sub(r"\s+", " ", markup).replace("> <", "><").strip()
    ok = hashlib.sha256(norm.encode("utf-8")).hexdigest() == NEXT_ICON_DIGEST
    return ok, "" if ok else "next-icon markup changed; flip it with CSS instead"


PLAN = [
    (
        {"width": 1280},
        [
            ("root_dir_lang", root_dir_lang, {}),
            (
                "computed_direction",
                computed_direction,
                {"selectors": ["body", tid("contact-text")]},
            ),
            ("on_side_logo", on_side, {"selector": tid("logo"), "side": "right"}),
            ("order_rtl_nav", order_rtl, {"selector": tid("nav-link")}),
            (
                "icon_next",
                icon_points,
                {"icon": tid("next-icon"), "head": "[data-part=head]", "want": "left"},
            ),
            ("bidi_phone", bidi_isolated, {"selectors": [tid("phone-text")]}),
            ("bidi_email", bidi_isolated, {"selectors": [tid("email-text")]}),
            (
                "input_name_ar",
                input_direction,
                {"selector": tid("name"), "text": NAME_AR, "want": "rtl"},
            ),
            (
                "input_name_latin",
                input_direction,
                {"selector": tid("name"), "text": "Sara", "want": "ltr"},
            ),
            (
                "input_email",
                input_direction,
                {"selector": tid("email-input"), "text": "a@b.co", "want": "ltr"},
            ),
            (
                "input_phone",
                input_direction,
                {"selector": tid("phone-input"), "text": "0791234567", "want": "ltr"},
            ),
            ("no_physical_css", no_physical_css, {}),
            ("arabic_text", arabic_text, {}),
            ("svg_markup_unchanged", svg_markup_unchanged, {}),
            ("elements_fit_1280", elements_fit, {}),
            ("no_overlays_1280", no_overlays, {}),
            ("no_effects_1280", no_effects, {}),
            ("readable_contrast_1280", readable_contrast, {}),
            ("no_shrink_tricks", no_shrink_tricks, {}),
        ],
    ),
    (
        {"width": 360},
        [
            ("no_horizontal_overflow_360", no_horizontal_overflow, {}),
            ("elements_fit_360", elements_fit, {}),
            ("no_overlays_360", no_overlays, {}),
            ("no_effects_360", no_effects, {}),
            ("readable_contrast_360", readable_contrast, {}),
            ("static_page", static_page, {}),
        ],
    ),
]

if __name__ == "__main__":
    results = grade(Path(sys.argv[1]), PLAN)
    print(json.dumps(results, sort_keys=True))
    sys.exit(0 if all(results.values()) else 1)
