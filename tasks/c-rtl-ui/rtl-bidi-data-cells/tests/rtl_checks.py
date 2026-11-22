"""Deterministic right-to-left checks for a web page, run in headless Chromium.

Canonical copy. Each RTL task vendors a byte-identical copy into its own tests/ folder
(never edit the vendored copy; edit this file and copy it over). Standard library plus the
Playwright sync API only, and no package-relative imports, so the file also runs on its own.

Checks read the DOM, computed styles and getBoundingClientRect only. Every check returns
(passed, short detail) and never raises; a selector that matches nothing is a failure.
"""

from __future__ import annotations

import mimetypes
import re
import sys
import unicodedata
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlparse

if TYPE_CHECKING:  # Playwright is imported lazily: the pure helpers work without it installed
    from playwright.sync_api import Page

ORIGIN = "http://kilmeh.local"
Result = tuple[bool, str]

_NO_ANIMATION = "* { transition: none !important; animation: none !important }"


def resolve_path(
    root: Path, url_path: str, overrides: dict[str, Path] | None = None
) -> Path | None:
    """Map a URL path to an existing file under root (or an override); else None.

    None covers a missing file, a path outside root, an override whose file is gone and
    hostile input such as `%00` (which would otherwise raise).
    """
    try:
        url_path = unquote(url_path) or "/"
        if overrides and url_path in overrides:
            target = overrides[url_path]
            return target if target.is_file() else None
        root = root.resolve()
        target = (root / url_path.lstrip("/")).resolve()
        if not target.is_relative_to(root):
            return None
        return target if target.is_file() else None
    except (ValueError, OSError):
        return None


def _content_type(path: Path) -> str:
    kind = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if kind.startswith("text/") or kind in ("application/javascript", "application/json"):
        kind += "; charset=utf-8"
    return kind


def launch_args() -> list[str]:
    """Chromium flags. --disable-dev-shm-usage: Docker gives Chromium a 64 MB /dev/shm."""
    return ["--disable-dev-shm-usage"]


@contextmanager
def open_page(
    root: Path,
    path: str = "/index.html",
    *,
    width: int = 1280,
    height: int = 800,
    overrides: dict[str, Path] | None = None,
    ready: str | None = None,
) -> Iterator[Page]:
    """Serve root from disk to headless Chromium; every request outside ORIGIN is aborted.

    HTTP requests are aborted and every WebSocket is mocked without connecting; both are listed
    on page.kilmeh_aborted. No port is opened and nothing leaves the machine, so a page that
    needs a CDN fails its checks instead of hanging.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=launch_args())
        try:
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=1,
                locale="ar-JO",
                timezone_id="UTC",
                reduced_motion="reduce",
                java_script_enabled=True,
            )
            aborted: list[str] = []

            def handle(route):
                url = route.request.url
                if not url.startswith(ORIGIN + "/"):
                    aborted.append(url)
                    route.abort()
                    return
                try:
                    file = resolve_path(root, urlparse(url).path, overrides)
                    body = file.read_bytes() if file else None
                except (ValueError, OSError):
                    body = None
                if body is None:
                    route.fulfill(status=404, body="not found", content_type="text/plain")
                else:
                    route.fulfill(status=200, body=body, content_type=_content_type(file))

            def handle_socket(ws):
                # Never connect_to_server(): the page talks to a mock and nothing reaches the
                # network. (ws.close() here crashes the Playwright 1.64.1 driver; verified.)
                aborted.append(ws.url)

            context.route("**/*", handle)
            context.route_web_socket("**/*", handle_socket)
            page = context.new_page()
            page.kilmeh_aborted = aborted
            page.goto(ORIGIN + path, wait_until="load")
            page.evaluate("document.fonts.ready.then(() => true)")
            if ready:
                page.wait_for_selector(ready, timeout=5000)
            page.evaluate(
                """(css) => {
                  const s = document.createElement('style');
                  s.setAttribute('data-kilmeh', '1');
                  s.textContent = css;
                  document.head.appendChild(s);
                }""",
                _NO_ANIMATION,
            )
            yield page
        finally:
            browser.close()


def _missing(selector: str) -> Result:
    return False, f"missing: {selector}"


def root_dir_lang(page: Page) -> Result:
    """<html dir> is rtl (case-insensitive) and <html lang> is ar or ar-*."""
    dir_, lang = page.evaluate(
        "[document.documentElement.getAttribute('dir') || '',"
        " document.documentElement.getAttribute('lang') || '']"
    )
    ok = dir_.lower() == "rtl" and re.fullmatch(r"ar(-[a-z0-9]+)*", lang, re.IGNORECASE) is not None
    return ok, f"dir={dir_!r} lang={lang!r}"


def computed_direction(page: Page, selectors: list[str], want: str = "rtl") -> Result:
    """Computed `direction` of every selector equals want."""
    got = page.evaluate(
        """(selectors) => selectors.map(s => {
          const el = document.querySelector(s);
          return el ? getComputedStyle(el).direction : null;
        })""",
        selectors,
    )
    for selector, value in zip(selectors, got, strict=True):
        if value is None:
            return _missing(selector)
        if value != want:
            return False, f"{selector} direction={value}, want {want}"
    return True, ""


# Shared by the geometry checks. visible(): box larger than `min`, not display:none, visibility
# hidden or opacity 0 on the element or any ancestor.
_VISIBLE_JS = """
const visible = (el, min = 0) => {
  const r = el.getBoundingClientRect();
  if (!(r.width > min && r.height > min)) return false;
  for (let e = el; e; e = e.parentElement) {
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || parseFloat(cs.opacity) === 0) return false;
    if (e === el && cs.visibility !== 'visible') return false;
  }
  return true;
};
"""

_OVERFLOW_JS = (
    """() => {
  """
    + _VISIBLE_JS
    + """
  const W = document.documentElement.clientWidth;
  const scrollW = document.documentElement.scrollWidth;
  const scrolls = (e) =>
    ['auto', 'scroll', 'hidden', 'clip'].includes(getComputedStyle(e).overflowX);
  const spill = [];
  for (const el of [document.body, ...document.body.querySelectorAll('*')]) {
    if (!visible(el, 1)) continue;
    if (getComputedStyle(el).position !== 'fixed') {
      let clipped = false;
      for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
        if (scrolls(p)) { clipped = true; break; }
      }
      if (clipped) continue;
    }
    const r = el.getBoundingClientRect();
    if (r.left < -1 || r.right > W + 1) {
      const cls = typeof el.className === 'string' ? el.className.split(' ')[0] : '';
      const name = el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (cls ? '.' + cls : '');
      spill.push(`${name} [${Math.round(r.left)}, ${Math.round(r.right)}]`);
    }
  }
  return {scrollW, W, spill};
}"""
)


def no_horizontal_overflow(page: Page) -> Result:
    """The page does not scroll sideways, and nothing visible sticks out of the viewport.

    Two passes (use at width=360). First scrollWidth <= clientWidth. That alone misses
    `overflow-x: hidden` on html/body, `position: fixed` boxes and RTL content clipped off
    the left edge, so the second pass walks every visible element (box over 1px, not
    display:none, visibility:hidden or opacity 0) that is not inside a scrolling container
    (overflow-x auto, scroll, hidden or clip) and fails any whose box extends more than 1px
    past the left or right edge. A scroller that is itself inside the viewport is fine.
    """
    got = page.evaluate(_OVERFLOW_JS)
    if got["scrollW"] > got["W"]:
        return False, f"scrollWidth={got['scrollW']} clientWidth={got['W']}"
    if got["spill"]:
        return False, "outside viewport: " + "; ".join(got["spill"][:6])
    return True, ""


_BOX_JS = (
    """(selectors) => {
  """
    + _VISIBLE_JS
    + """
  const W = document.documentElement.clientWidth;
  return {W, items: selectors.map(s => [...document.querySelectorAll(s)].map(el => {
    const r = el.getBoundingClientRect();
    return {left: r.left, right: r.right, visible: visible(el)};
  }))};
}"""
)


def _seen(item: dict, width: float) -> bool:
    """Visible, non-zero size and horizontally inside the viewport."""
    return item["visible"] and item["right"] > 0 and item["left"] < width


def on_side(page: Page, selector: str, side: str) -> Result:
    """The first match is visible, in the viewport, and its centre is on the `side` half."""
    got = page.evaluate(_BOX_JS, [selector])
    items, width = got["items"][0], got["W"]
    if not items:
        return _missing(selector)
    item = items[0]
    if not _seen(item, width):
        return False, f"{selector} is not visible inside the viewport"
    centre = (item["left"] + item["right"]) / 2
    ok = centre > width / 2 if side == "right" else centre < width / 2
    return ok, f"{selector} centre x={centre:.0f} of {width}, want {side}"


def order_rtl(page: Page, selector: str) -> Result:
    """Two or more matches, all visible and in view, centres strictly decreasing in DOM order."""
    got = page.evaluate(_BOX_JS, [selector])
    items, width = got["items"][0], got["W"]
    if len(items) < 2:
        return False, f"need at least 2 matches for {selector}, got {len(items)}"
    hidden = [i for i, it in enumerate(items) if not _seen(it, width)]
    if hidden:
        return False, f"{selector} item(s) {hidden} not visible inside the viewport"
    centres = [(it["left"] + it["right"]) / 2 for it in items]
    ok = all(x > y for x, y in zip(centres, centres[1:], strict=False))
    return ok, f"{selector} centres {[round(c) for c in centres]}"


_MIRROR_JS = """async (selectors) => {
  const root = document.documentElement;
  const original = root.getAttribute('dir');
  const frames = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const boxes = () => selectors.map(s => {
    const el = document.querySelector(s);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {left: r.left, right: r.right, width: r.width};
  });
  try {
    root.setAttribute('dir', 'rtl');
    await frames();
    const rtl = boxes();
    root.setAttribute('dir', 'ltr');
    await frames();
    const ltr = boxes();
    return {rtl, ltr, width: root.clientWidth};
  } finally {
    if (original === null) root.removeAttribute('dir'); else root.setAttribute('dir', original);
  }
}"""


def mirror_on_dir_flip(page: Page, selectors: list[str], tol: float = 2.0) -> Result:
    """Flipping only <html dir> to ltr mirrors each box: l_rtl == W - r_ltr, same width.

    Limit: a box that is symmetric about the page centre (a centred column, margin: 0 auto)
    mirrors onto itself under any layout, so the check is vacuous for it. Graded elements must
    be asymmetric: pick ones that sit toward a side (logo, sign-in button, a nav link).
    """
    got = page.evaluate(_MIRROR_JS, selectors)
    width = got["width"]
    for selector, a, b in zip(selectors, got["rtl"], got["ltr"], strict=True):
        if a is None or b is None:
            return _missing(selector)
        if abs(a["left"] - (width - b["right"])) > tol or abs(a["width"] - b["width"]) > tol:
            return False, (
                f"{selector} not mirrored: rtl left={a['left']:.0f} w={a['width']:.0f}, "
                f"ltr right={b['right']:.0f} w={b['width']:.0f}, W={width:.0f}"
            )
    return True, ""


PHYSICAL_PAIRS = [
    ("margin-left", "margin-right"),
    ("padding-left", "padding-right"),
    ("left", "right"),
    ("border-left-width", "border-right-width"),
    ("border-left-color", "border-right-color"),
    ("border-left-style", "border-right-style"),
    ("border-top-left-radius", "border-top-right-radius"),
    ("border-bottom-left-radius", "border-bottom-right-radius"),
    ("scroll-margin-left", "scroll-margin-right"),
    ("scroll-padding-left", "scroll-padding-right"),
]

# Static pass: every same-origin style sheet (recursing into @media, @supports, @layer and
# @import), constructed sheets in document.adoptedStyleSheets, <style> and [style] inside open
# shadow roots, and every [style] attribute. Logical properties are separate longhands in the
# CSSOM, so they never fill margin-left and friends; a shorthand like `margin: 0 auto` expands
# to equal sides. Computed pass: every visible element, so `text-align: var(--s)` with
# `--s: left` is caught even though the rule text does not say left.
_PHYSICAL_CSS_JS = (
    """([pairs, allow]) => {
  """
    + _VISIBLE_JS
    + """
  const norm = (v) => v.replace(/^-webkit-/, '');
  const zero = (v) => /^0(\\.0+)?([a-z%]+)?$/.test(v);
  const allowedRule = (sel) => sel.split(',').some(p => allow.includes(p.trim()));
  const allowedEl = (el) => allow.some(s => {
    try { return el.matches(s); } catch (e) { return false; }
  });
  const sides = ['text-align', 'text-align-last', 'float', 'clear'];
  const offenders = [];
  const inspect = (label, style) => {
    for (const [a, b] of pairs) {
      const va = style.getPropertyValue(a), vb = style.getPropertyValue(b);
      if (va === vb) continue;
      // a lone zero is symmetric (margin-left: 0), except left/right which pin a box to a side
      if (a !== 'left' && (va === '' || zero(va)) && (vb === '' || zero(vb))) continue;
      offenders.push(`${label} {${a}: ${va || '(unset)'}; ${b}: ${vb || '(unset)'}}`);
    }
    for (const prop of sides) {
      const v = norm(style.getPropertyValue(prop));
      if (v === 'left' || v === 'right') offenders.push(`${label} {${prop}: ${v}}`);
    }
  };
  const isOurs = (sheet) => sheet.ownerNode && sheet.ownerNode.hasAttribute
    && sheet.ownerNode.hasAttribute('data-kilmeh');
  const walkSheet = (sheet) => {
    if (isOurs(sheet)) return;
    let rules;
    try { rules = sheet.cssRules; } catch (e) { return; }
    walk(rules);
  };
  const walk = (rules) => {
    for (const rule of rules) {
      if (rule.selectorText !== undefined && rule.style && !allowedRule(rule.selectorText)) {
        inspect(rule.selectorText, rule.style);
      }
      if (rule.styleSheet) walkSheet(rule.styleSheet);
      if (rule.cssRules && !(rule instanceof CSSKeyframesRule)) walk(rule.cssRules);
    }
  };
  const roots = [document];
  const collect = (node) => {
    for (const el of node.querySelectorAll('*')) {
      if (el.shadowRoot) { roots.push(el.shadowRoot); collect(el.shadowRoot); }
    }
  };
  collect(document);
  for (const root of roots) {
    for (const sheet of [...root.styleSheets, ...root.adoptedStyleSheets]) walkSheet(sheet);
    for (const el of root.querySelectorAll('[style]')) {
      if (!allowedEl(el)) inspect(`[style] <${el.tagName.toLowerCase()}>`, el.style);
    }
    for (const el of root.querySelectorAll('*')) {
      if (!visible(el) || allowedEl(el)) continue;
      const cs = getComputedStyle(el);
      for (const prop of sides) {
        const v = norm(cs.getPropertyValue(prop));
        if (v === 'left' || v === 'right') {
          offenders.push(`computed <${el.tagName.toLowerCase()}> {${prop}: ${v}}`);
        }
      }
    }
  }
  return offenders;
}"""
)


def no_physical_css(page: Page, allow: Sequence[str] = ()) -> Result:
    """No asymmetric left/right CSS and no text-align/float/clear of left or right.

    A rule is flagged when one side of a PHYSICAL_PAIRS pair is set without the other (a lone
    zero is fine, except for left/right) or the two values differ, or when text-align,
    text-align-last, float or clear is left, right or -webkit-left/right. Covers linked and
    @import-ed sheets, adopted sheets, shadow roots and inline styles, plus a computed-style
    pass over visible elements (catches var() values). Selectors in `allow` are skipped: a rule
    is skipped when any selector of its list is in `allow`; an element is skipped when it
    matches one.

    Decision, not graded: `background-position: left|right` and @keyframes. Both are visual
    detail with no layout effect on direction, and flagging them would fail valid solutions;
    revisit with the deferred checks.
    """
    offenders = page.evaluate(_PHYSICAL_CSS_JS, [PHYSICAL_PAIRS, list(allow)])
    return not offenders, "; ".join(offenders[:8])


# Real Tailwind value forms only: numbers, fractions, px, auto, full, arbitrary [..] and (..),
# plus the default radius and colour names. So a project class like `left-nav` or `pr-card` is
# not flagged here (a compiled physical rule would still fail no_physical_css).
_NUM = r"\d+(\.\d+)?"
_VAL = rf"(-?{_NUM}|{_NUM}/{_NUM}|px|auto|full|\[.+\]|\(.+\))"
_RADIUS = r"(none|xs|sm|md|lg|xl|2xl|3xl|4xl|full|\[.+\]|\(.+\))"
_COLOUR = (
    r"((slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky"
    r"|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}|black|white|transparent|current"
    r"|inherit)(/\d+)?"
)
_BORDER = rf"({_NUM}|px|\[.+\]|\(.+\)|{_COLOUR})"
_ARBITRARY = (
    r"\[(margin|padding|scroll-margin|scroll-padding)-(left|right):.+\]"
    r"|\[(left|right):.+\]|\[border-(left|right)(-[a-z]+)*:.+\]"
    r"|\[border-(top|bottom)-(left|right)-radius:.+\]"
    r"|\[(text-align|text-align-last|float|clear):(left|right)\]"
)
_TAILWIND_PHYSICAL = re.compile(
    rf"-?[mp][lr]-{_VAL}|-?(left|right)-{_VAL}|text-(left|right)|float-(left|right)"
    rf"|clear-(left|right)|rounded-([lr]|tl|tr|bl|br)(-{_RADIUS})?|border-[lr](-{_BORDER})?"
    rf"|scroll-[mp][lr]-{_VAL}|{_ARBITRARY}"
)


def _split_variants(token: str) -> tuple[list[str], str]:
    """Split `md:hover:ml-4` into (['md', 'hover'], 'ml-4'); brackets keep their colons."""
    parts, depth, start = [], 0, 0
    for i, ch in enumerate(token):
        if ch in "[(":
            depth += 1
        elif ch in "])":
            depth -= 1
        elif ch == ":" and depth == 0:
            parts.append(token[start:i])
            start = i + 1
    return parts, token[start:].strip("!")


def physical_tailwind_classes(tokens: list[str]) -> list[str]:
    """The Tailwind utilities that hard-code a physical side (ml-4, pr-2, [margin-left:4px]).

    Variants are stripped (md:, hover:, rtl:), but an `ltr:` variant allows the class: it only
    applies to left-to-right pages. `space-x-*` is not flagged: Tailwind v4 emits
    margin-inline-start/end for it (checked in tailwindcss 4.1.0, dist/lib.js).
    """
    flagged = []
    for token in tokens:
        variants, utility = _split_variants(token)
        if "ltr" not in variants and _TAILWIND_PHYSICAL.fullmatch(utility):
            flagged.append(token)
    return flagged


def no_physical_tailwind(page: Page) -> Result:
    """No class token in the rendered DOM is a physical-side Tailwind utility."""
    tokens = page.evaluate(
        """() => [...new Set([...document.querySelectorAll('[class]')]
          .flatMap(el => (el.getAttribute('class') || '').split(/\\s+/).filter(Boolean)))]"""
    )
    bad = physical_tailwind_classes(tokens)
    return not bad, "physical classes: " + " ".join(sorted(bad)[:12]) if bad else ""


def icon_points(page: Page, icon: str, head: str, want: str) -> Result:
    """The icon's `head` part sits on the `want` ("left" or "right") side of the icon's centre.

    Uses bounding boxes, so it follows CSS transforms (scaleX(-1)) and not the SVG source.
    """
    got = page.evaluate(
        """([icon, head]) => {
          const el = document.querySelector(icon);
          if (!el) return 'icon';
          const part = el.querySelector(head);
          if (!part) return 'head';
          const a = el.getBoundingClientRect(), b = part.getBoundingClientRect();
          return (b.left + b.right) / 2 - (a.left + a.right) / 2;
        }""",
        [icon, head],
    )
    if got == "icon":
        return _missing(icon)
    if got == "head":
        return _missing(f"{icon} {head}")
    side = "right" if got > 0.5 else "left" if got < -0.5 else "centre"
    return side == want, f"{icon} head is {side} of centre ({got:+.1f}px), want {want}"


_ISOLATING = ["isolate", "isolate-override", "plaintext"]

# A run counts as isolated when the element is, or every piece of its text sits inside an
# isolating descendant (<bdi>, any [dir], computed unicode-bidi), or its text is wrapped in
# Unicode isolate controls (LRI, RLI or FSI, closed by PDI).
_BIDI_JS = """([selectors, isolating]) => selectors.map(s => {
  const el = document.querySelector(s);
  if (!el) return null;
  const isolates = (e) =>
    isolating.includes(getComputedStyle(e).unicodeBidi) || e.hasAttribute('dir');
  if (isolates(el)) return 'self';
  const text = el.textContent.trim();
  if (/^[\\u2066\\u2067\\u2068][^]*\\u2069$/.test(text)) return 'controls';
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  let found = false;
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    if (!n.nodeValue.trim()) continue;
    let inside = false;
    for (let e = n.parentElement; e && e !== el; e = e.parentElement) {
      if (isolates(e)) { inside = true; break; }
    }
    if (!inside) return 'exposed';
    found = true;
  }
  return found ? 'descendant' : 'exposed';
})"""


def bidi_isolated(page: Page, selectors: list[str]) -> Result:
    """Each run is isolated from the surrounding text.

    Pass when the element's computed unicode-bidi is isolate, isolate-override or plaintext
    (covers <bdi> and any [dir]), or all its text sits inside such a descendant, or the text is
    wrapped in U+2066/2067/2068 ... U+2069. `unicode-bidi: embed` and plain spans fail.
    """
    got = page.evaluate(_BIDI_JS, [selectors, _ISOLATING])
    for selector, how in zip(selectors, got, strict=True):
        if how is None:
            return _missing(selector)
        if how == "exposed":
            return False, f"{selector} is not isolated (no isolate on it, inside it or around it)"
    return True, ""


_INPUT_JS = """([selector, want]) => {
  const el = document.querySelector(selector);
  const cs = getComputedStyle(el);
  // :dir() only counts for dir=auto (resolved from the text); for a fixed dir attribute it would
  // ignore a CSS direction override that really decides how the field reads
  const auto = (el.getAttribute('dir') || '').toLowerCase() === 'auto';
  return [auto && el.matches(`:dir(${want})`), cs.direction, cs.unicodeBidi];
}"""


def _text_direction(text: str) -> str:
    """Direction of the first strong character, as unicode-bidi: plaintext decides it."""
    for ch in text:
        kind = unicodedata.bidirectional(ch)
        if kind == "L":
            return "ltr"
        if kind in ("R", "AL"):
            return "rtl"
    return "ltr"


def input_direction(page: Page, selector: str, text: str, want: str) -> Result:
    """After typing `text`, the field reads in direction `want`.

    Pass if the computed `direction` is want (a dir attribute or CSS direction), or, for a
    field with `unicode-bidi: plaintext`, the typed text's own direction is want (the computed
    `direction` is ignored then), or the field is dir=auto and matches :dir(want) (resolved
    from the text). A plain :dir() match is not enough: it follows the dir attribute and
    ignores a CSS direction override.
    """
    if page.locator(selector).count() == 0:
        return _missing(selector)
    try:
        page.fill(selector, text, timeout=2000)
    except Exception as exc:  # not fillable
        return False, f"cannot fill {selector}: {str(exc).splitlines()[0]}"
    matches, computed, bidi = page.evaluate(_INPUT_JS, [selector, want])
    # under plaintext the text decides, whatever `direction` says
    effective = _text_direction(text) if bidi == "plaintext" else computed
    ok = effective == want or matches
    return ok, f"{selector} direction={computed} unicode-bidi={bidi} :dir({want})={matches}"


_FITS_JS = (
    """(selector) => {
  """
    + _VISIBLE_JS
    + """
  const el = document.querySelector(selector);
  if (!el) return null;
  const W = document.documentElement.clientWidth;
  const r = el.getBoundingClientRect();
  const out = {visible: visible(el), scroll: el.scrollWidth, client: el.clientWidth,
               left: r.left, right: r.right, W, clippedBy: null};
  for (let p = el.parentElement; p && p !== document.documentElement; p = p.parentElement) {
    if (getComputedStyle(p).overflowX === 'visible') continue;
    const pr = p.getBoundingClientRect();
    if (r.left < pr.left - 1 || r.right > pr.right + 1) {
      out.clippedBy = p.tagName.toLowerCase();
      break;
    }
  }
  return out;
}"""
)


def fits_width(page: Page, selector: str) -> Result:
    """The element is visible, its own content is not cut off, and its box fits the page.

    Fails when scrollWidth exceeds clientWidth, when the box sticks out of the viewport, or
    when an ancestor with overflow-x other than visible clips it (a table hidden by
    `overflow-x: hidden` on its container is still too wide).
    """
    got = page.evaluate(_FITS_JS, selector)
    if got is None:
        return _missing(selector)
    if not got["visible"]:
        return False, f"{selector} is not visible"
    if got["scroll"] > got["client"]:
        return False, f"{selector} scrollWidth={got['scroll']} clientWidth={got['client']}"
    if got["left"] < -1 or got["right"] > got["W"] + 1:
        return False, f"{selector} box [{got['left']:.0f}, {got['right']:.0f}] of {got['W']}"
    if got["clippedBy"]:
        return False, f"{selector} is clipped by <{got['clippedBy']}>"
    return True, ""


_ORDER_JS = (
    """([selector, tokens]) => {
  """
    + _VISIBLE_JS
    + """
  const el = document.querySelector(selector);
  if (!el) return null;
  el.scrollIntoView({block: 'center'});
  const nodes = [], starts = [];
  let full = '';
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    starts.push(full.length); nodes.push(n); full += n.nodeValue;
  }
  // a flipped box (negative x or y scale, any rotation) shows mirrored glyphs: never readable
  const flipped = (e) => {
    const cs = getComputedStyle(e);
    if (cs.transform !== 'none') {
      const m = new DOMMatrix(cs.transform);
      if (m.a < 0 || m.d < 0) return true;
    }
    if (cs.scale !== 'none' && cs.scale.split(/\\s+/).some((v) => parseFloat(v) < 0)) return true;
    return cs.rotate !== 'none' && cs.rotate !== '0deg';
  };
  const out = [];
  let from = 0;
  for (const tok of tokens) {
    const i = full.indexOf(tok, from);
    if (i < 0) return {error: `"${tok}" not found in order in the text`};
    from = i + tok.length;
    let k = starts.length - 1;
    while (starts[k] > i) k--;
    const off = i - starts[k], node = nodes[k], host = node.parentElement;
    if (off + tok.length > node.nodeValue.length) return {error: `"${tok}" is split`};
    for (let e = host; e; e = e.parentElement) {
      if (flipped(e)) return {error: `"${tok}" is mirrored by a transform`};
    }
    const range = document.createRange();
    range.setStart(node, off); range.setEnd(node, off + tok.length);
    const r = range.getBoundingClientRect();
    const hit = r.width > 0 ? document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2)
                            : null;
    if (!visible(host) || !hit || !(hit === host || host.contains(hit)))
      return {error: `"${tok}" is not visible on screen`};
    // the token's own letters must not be reversed (bidi-override): an Arabic token's first
    // letter sits right of its last, any other token's first character left of its last
    if (tok.length > 1) {
      const mid = (j) => {
        const c = document.createRange();
        c.setStart(node, off + j); c.setEnd(node, off + j + 1);
        const b = c.getBoundingClientRect();
        return b.left + b.width / 2;
      };
      const a = mid(0), z = mid(tok.length - 1);
      if (/[\\u0600-\\u06ff]/.test(tok[0]) ? !(a > z) : !(a < z))
        return {error: `"${tok}" has its letters reversed`};
    }
    out.push({x: r.left + r.width / 2, y: r.top + r.height / 2, h: r.height});
  }
  return out;
}"""
)


def visual_order(page: Page, selector: str, tokens: list[str], want: str) -> Result:
    """The tokens, found in this order in the element's text, read in direction `want`.

    Each token must sit inside one text node, be visible and not covered (hit test at its
    centre), and all tokens must share one line. Pass when their centres run left to right
    (want="ltr") or right to left (want="rtl") on screen. Mirroring by transform, scale or
    rotate fails, so a flipped box cannot fake the order, and so does a multi-character token
    whose own characters are reversed (an Arabic token reads right to left, any other token left
    to right). Raises ValueError for fewer than 2 tokens or a `want` other than ltr or rtl.
    """
    if len(tokens) < 2:
        raise ValueError("visual_order needs at least 2 tokens")
    if want not in ("ltr", "rtl"):
        raise ValueError(f"want must be 'ltr' or 'rtl', not {want!r}")
    got = page.evaluate(_ORDER_JS, [selector, tokens])
    if got is None:
        return _missing(selector)
    if isinstance(got, dict):
        return False, f"{selector}: {got['error']}"
    first = got[0]
    if any(abs(t["y"] - first["y"]) > first["h"] / 2 for t in got):
        return False, f"{selector}: tokens are not on one line"
    xs = [t["x"] for t in got]
    pairs = list(zip(xs, xs[1:], strict=False))
    ok = all(a < b for a, b in pairs) if want == "ltr" else all(a > b for a, b in pairs)
    return ok, f"{selector} token x={[round(x) for x in xs]}, want {want}"


DIRECTION_MARKS = "⁦⁧⁨⁩‎‏"  # LRI RLI FSI PDI LRM RLM


def visible_text(text: str) -> str:
    """Text without invisible direction marks and without any whitespace.

    All whitespace goes, because reformatting HTML adds whitespace to textContent that never
    renders; reordered or changed words still differ.
    """
    return "".join(text.translate({ord(c): None for c in DIRECTION_MARKS}).split())


def testid_texts(html: str) -> dict[str, str]:
    """textContent (as visible_text) of every element with a data-testid in an HTML string."""
    from html.parser import HTMLParser

    void = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source"}

    class Collect(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack: list[str | None] = []
            self.parts: dict[str, list[str]] = {}

        def handle_starttag(self, tag, attrs):
            if tag in void:
                return
            testid = dict(attrs).get("data-testid")
            if testid:
                self.parts[testid] = []
            self.stack.append(testid)

        def handle_endtag(self, tag):
            if tag not in void and self.stack:
                self.stack.pop()

        def handle_data(self, data):
            for testid in self.stack:
                if testid:
                    self.parts[testid].append(data)

    parser = Collect()
    parser.feed(html)
    return {k: visible_text("".join(v)) for k, v in parser.parts.items()}


def text_kept(page: Page, expected: dict[str, str]) -> Result:
    """Each [data-testid] element's text equals expected, ignoring only invisible direction marks
    (U+2066-2069, U+200E, U+200F) and all whitespace (see visible_text)."""
    got = page.evaluate(
        """(ids) => ids.map(id => {
          const el = document.querySelector(`[data-testid="${id}"]`);
          return el ? el.textContent : null;
        })""",
        list(expected),
    )
    for testid, text in zip(expected, got, strict=True):
        if text is None:
            return _missing(f'[data-testid="{testid}"]')
        if visible_text(text) != visible_text(expected[testid]):
            return False, f"{testid}: text changed"
    return True, ""


Check = tuple[str, Callable[..., Result], dict]  # (key, fn, kwargs)


def grade(root: Path, plan: list[tuple[dict, list[Check]]]) -> dict[str, bool]:
    """Run each (open_page kwargs, checks) group on a fresh page; return {key: passed}.

    A check that raises is False, and so is every check of a group whose page cannot open.
    Duplicate keys are rejected before anything runs. Details go to stderr.
    """
    keys = [key for _, checks in plan for key, _, _ in checks]
    dupes = sorted({k for k in keys if keys.count(k) > 1})
    if dupes:
        raise ValueError(f"duplicate check keys: {dupes}")
    results: dict[str, bool] = {}

    def record(key: str, ok: bool, detail: str) -> None:
        results[key] = ok
        print(f"{'PASS' if ok else 'FAIL'} {key}: {detail}", file=sys.stderr)

    for page_kwargs, checks in plan:
        try:
            with open_page(root, **page_kwargs) as page:
                for key, fn, kwargs in checks:
                    try:
                        ok, detail = fn(page, **kwargs)
                    except Exception as exc:
                        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
                    record(key, bool(ok), detail)
        except Exception as exc:
            for key, _, _ in checks:
                if key not in results:
                    record(key, False, f"page failed to open: {type(exc).__name__}: {exc}")
    return results
