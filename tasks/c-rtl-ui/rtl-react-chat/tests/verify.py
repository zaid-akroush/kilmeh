"""Grade rtl-react-chat. Usage: python3 -I verify.py APP OUT

Prints one boolean per check as JSON and exits 0 only if every check passes. OUT holds
`app.js` (and `app.css`, when CSS is imported from JS), rebuilt from APP/src by build.sh with the
image's own toolchain under /opt; they are served in place of /dist/app.js and /dist/app.css, so
an edited APP/dist or APP/node_modules is never graded. The Arabic typed into the composer is `composer_sample.txt`, copied
from the fixture's placeholder bytes (never retyped).
"""

import json
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # -I drops the script dir

from rtl_checks import (  # noqa: E402
    _VISIBLE_JS,
    fits_width,
    grade,
    input_direction,
    mirror_on_dir_flip,
    no_horizontal_overflow,
    no_physical_css,
    root_dir_lang,
    bidi_isolated,
)

COMPOSER_AR = (HERE / "composer_sample.txt").read_text(encoding="utf-8")
ME = '[data-testid="bubble-me"]'
THEM = '[data-testid="bubble-them"]'
AVATAR = '[data-testid="avatar"]'
CARD = '[data-testid="order-card"]'
COMPOSER = '[data-testid="composer"]'
MIN_ME, MIN_THEM = 2, 2  # bubbles in the fixture; adding more is fine, removing is not
BUNDLE = "/dist/app.js"
STYLES = "/dist/app.css"  # CSS imported from JS; served from the build, never from dist/
TOOLCHAIN = Path("/opt/kilmeh-build")

_SIDES_JS = (
    """([me, them, avatar]) => {
  """
    + _VISIBLE_JS
    + """
  const W = document.documentElement.clientWidth;
  const box = (el) => {
    const r = el.getBoundingClientRect();
    return {centre: (r.left + r.right) / 2, inView: r.right > 0 && r.left < W, ok: visible(el)};
  };
  const all = (s) => [...document.querySelectorAll(s)].map(box);
  const pairs = [...document.querySelectorAll(avatar)].map(a => {
    let e = a.parentElement;
    while (e && !e.querySelector(them)) e = e.parentElement;
    const bubbles = e ? e.querySelectorAll(them) : [];
    // the nearest ancestor that holds a bubble must hold exactly one: the avatar's own
    return {avatar: box(a), bubble: bubbles.length === 1 ? box(bubbles[0]) : null};
  });
  return {W, me: all(me), them: all(them), pairs};
}"""
)


def _sides(page):
    return page.evaluate(_SIDES_JS, [ME, THEM, AVATAR])


def _bubbles(page, key: str, minimum: int, side: str):
    got = _sides(page)
    items, width = got[key], got["W"]
    if len(items) < minimum:
        return False, f"need at least {minimum} {key} bubbles, got {len(items)}"
    for i, item in enumerate(items):
        if not (item["ok"] and item["inView"]):
            return False, f"{key} bubble {i} is not visible inside the viewport"
        right = item["centre"] > width / 2
        if right != (side == "right"):
            return False, f"{key} bubble {i} centre x={item['centre']:.0f} of {width}, want {side}"
    return True, ""


def bubbles_me_left(page):
    """Every own bubble sits on the left half (the RTL chat convention), visible, in view."""
    return _bubbles(page, "me", MIN_ME, "left")


def bubbles_them_right(page):
    """Every incoming bubble sits on the right half, visible, in view."""
    return _bubbles(page, "them", MIN_THEM, "right")


def avatar_at_start(page):
    """Each avatar is visible, on the right half, and right of the bubble it belongs to."""
    got = _sides(page)
    pairs, width = got["pairs"], got["W"]
    if len(pairs) < MIN_THEM:
        return False, f"need at least {MIN_THEM} avatars, got {len(pairs)}"
    for i, pair in enumerate(pairs):
        avatar, bubble = pair["avatar"], pair["bubble"]
        if bubble is None:
            return False, f"avatar {i}: cannot pair it with exactly one bubble-them"
        if not (avatar["ok"] and avatar["inView"] and bubble["ok"]):
            return False, f"avatar {i} or its bubble is not visible inside the viewport"
        if not (avatar["centre"] > width / 2 and avatar["centre"] > bubble["centre"]):
            return False, (
                f"avatar {i} centre x={avatar['centre']:.0f}, its bubble {bubble['centre']:.0f}"
                f" of {width}: the avatar must be at the start (right) side"
            )
    return True, ""


_SHRINK_JS = """(selector) => {
  const el = document.querySelector(selector);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  const out = {layout: el.offsetWidth, drawn: r.width, shrunk: null};
  for (let e = el; e; e = e.parentElement) {
    const cs = getComputedStyle(e);
    if (cs.transform !== 'none' || cs.scale !== 'none' || cs.rotate !== 'none'
        || cs.translate !== 'none' || (cs.zoom && parseFloat(cs.zoom) !== 1)) {
      out.shrunk = e.tagName.toLowerCase();
      break;
    }
  }
  return out;
}"""


def card_fits(page):
    """The order-details card fits the screen as laid out: not clipped, not shrunk.

    fits_width (visible, no sideways scroll, inside the viewport, no clipping ancestor) plus:
    no transform, scale, rotate, translate or zoom on the card or an ancestor, drawn width equal
    to layout width, and at least 200px wide (a collapsed card does not count as fitting).
    """
    ok, detail = fits_width(page, CARD)
    if not ok:
        return ok, detail
    got = page.evaluate(_SHRINK_JS, CARD)
    if got["shrunk"]:
        return False, f"{CARD} is shrunk or moved by a transform/zoom on <{got['shrunk']}>"
    if abs(got["layout"] - got["drawn"]) > 1:
        return False, f"{CARD} layout width {got['layout']} != drawn {got['drawn']:.0f}"
    if got["drawn"] < 200:
        return False, f"{CARD} is only {got['drawn']:.0f}px wide"
    return True, ""


def bundle_is_built_output(page):
    """The page runs only the bundle that build.sh makes from src/: one script, /dist/app.js."""
    srcs = page.evaluate("[...document.scripts].map(s => s.src ? new URL(s.src).pathname : null)")
    if srcs != [BUNDLE]:
        return False, f"scripts on the page: {srcs}; want exactly [{BUNDLE!r}]"
    return True, ""


BASE_URL = "http://kilmeh.local/index.html"
ALLOWED_STYLES = {"/dist/app.css", "/src/styles.css"}  # built CSS, or the source stylesheet
ALLOWED_REQUESTS = {"/index.html", BUNDLE, *ALLOWED_STYLES}
VOID = ("meta", "link")
# element -> attributes it may carry. Anything else, anywhere, fails.
ALLOWED_ATTRS = {
    "html": {"lang", "dir"},
    "head": set(),
    "meta": {"charset", "name", "content"},
    "title": set(),
    "link": {"rel", "href"},
    "script": {"src", "defer"},
    "body": set(),
    "div": {"id"},
}


def _path(url: str) -> str:
    return urlparse(urljoin(BASE_URL, url)).path


class _Scan(HTMLParser):
    """Checks index.html against an allow-list, before any script can run."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.problems: list[str] = []
        self.stack: list[str] = []
        self.scripts = 0
        self.links = 0
        self.divs = 0

    def bad(self, text: str) -> None:
        self.problems.append(text)

    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED_ATTRS:
            self.bad(f"<{tag}> is not allowed")
            self.stack.append(tag)
            return
        names = {n for n, _ in attrs}
        extra = names - ALLOWED_ATTRS[tag]
        if extra:
            self.bad(f"<{tag}> attribute(s) not allowed: {sorted(extra)}")
        a = {n: v or "" for n, v in attrs}
        if tag == "meta":
            charset = names == {"charset"}
            viewport = a.get("name") == "viewport" and names <= {"name", "content"}
            if not (charset or viewport):
                self.bad("<meta> may only set charset or name=viewport")
        elif tag == "link":
            self.links += 1
            if a.get("rel") != "stylesheet" or _path(a.get("href", "")) not in ALLOWED_STYLES:
                self.bad(f"<link> must be rel=stylesheet to one of {sorted(ALLOWED_STYLES)}")
        elif tag == "script":
            self.scripts += 1
            if "src" not in a or _path(a["src"]) != BUNDLE:
                self.bad(f"<script> src must resolve to {BUNDLE}")
        elif tag == "div":
            self.divs += 1
            if names != {"id"} or not a.get("id"):
                self.bad("the root <div> needs exactly an id")
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_data(self, data):
        if not data.strip():
            return
        if self.stack and self.stack[-1] == "title":
            return
        self.bad("text outside <title> (inline script content included)")

    def handle_decl(self, decl):
        if decl.strip().lower() != "doctype html":
            self.bad(f"declaration <!{decl}>")

    def handle_pi(self, data):
        self.bad("processing instruction")

    def unknown_decl(self, data):
        self.bad("unknown declaration")


def static_index(page, root: Path):
    """The index.html bytes the grader serves, read before any JS runs, against an allow-list.

    Elements: html, head, meta (charset or viewport only), title, at most one link
    rel=stylesheet (/dist/app.css or the source /src/styles.css), exactly one script whose src is
    /dist/app.js (no inline content), body and the root div. Attributes per element are listed in
    ALLOWED_ATTRS; text may only be whitespace (and the title). So no iframe, object, embed,
    template, svg, base, other link, meta http-equiv, event handler or javascript: URL.
    """
    scan = _Scan()
    scan.feed((root / "index.html").read_text(encoding="utf-8", errors="replace"))
    scan.close()
    if scan.scripts != 1:
        scan.bad(f"need exactly one <script>, found {scan.scripts}")
    if scan.links > 1:
        scan.bad("at most one <link>")
    if scan.divs != 1:
        scan.bad(f"need exactly one root <div>, found {scan.divs}")
    if scan.problems:
        return False, "index.html: " + "; ".join(scan.problems[:4])
    return True, ""


def requests_allowed(page):
    """Loading the page again, with request events recorded from the first byte, asks only for
    /index.html, /dist/app.js and the stylesheet; no extra frame, no other document request.

    Covers same-origin iframes, fetch plus eval of a hidden file and modulepreload. Requests the
    sandbox aborts (anything off-origin) are on page.kilmeh_aborted and fail too.
    """
    if page.kilmeh_aborted:
        return False, f"blocked external requests: {page.kilmeh_aborted[:3]}"
    second = page.context.new_page()
    seen: list[tuple[str, str, bool]] = []
    second.on(
        "request",
        lambda r: seen.append((r.url, r.resource_type, r.frame == second.main_frame)),
    )
    try:
        second.goto(BASE_URL, wait_until="load")
        second.wait_for_selector('[data-testid="chat-ready"]', timeout=5000)
        second.wait_for_load_state("networkidle")
        second.wait_for_timeout(500)
        frames = len(second.frames)
    finally:
        second.close()
    extra = sorted({u for u, _, _ in seen if _path(u) not in ALLOWED_REQUESTS})
    if extra:
        return False, f"requests outside the allow-list: {extra[:4]}"
    docs = [u for u, kind, main in seen if kind == "document" and not main]
    if docs or frames > 1:
        return False, f"extra frame(s): {frames}, document requests {docs[:3]}"
    return True, ""


def toolchain_intact(page):
    """esbuild, react, react-dom and scheduler under /opt are the files the image was built with.

    digest.py (written into the image next to the toolchain) recomputes the sha256 of each file;
    the result must equal /opt/kilmeh-build/DIGESTS, recorded when the image was built.
    """
    try:
        now = subprocess.run(
            ["python3", "-I", str(TOOLCHAIN / "digest.py"), str(TOOLCHAIN)],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        ).stdout
        recorded = (TOOLCHAIN / "DIGESTS").read_text(encoding="utf-8")
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"cannot verify the toolchain: {exc}"
    if now != recorded:
        changed = sorted(set(now.splitlines()) ^ set(recorded.splitlines()))
        return False, "toolchain differs from the image build: " + "; ".join(changed[:4])
    return True, ""


def plan(root: Path, out: Path) -> list:
    return [
        (
            {
                "width": 360,
                "overrides": {BUNDLE: out / "app.js", STYLES: out / "app.css"},
                "ready": '[data-testid="chat-ready"]',
            },
            [
                ("root_dir_lang", root_dir_lang, {}),
                ("bubbles_me_left", bubbles_me_left, {}),
                ("bubbles_them_right", bubbles_them_right, {}),
                ("avatar_at_start", avatar_at_start, {}),
                (
                    "bidi_isolated",
                    bidi_isolated,
                    {"selectors": ['[data-testid="product"]', '[data-testid="order"]']},
                ),
                (
                    "input_composer_ar",
                    input_direction,
                    {"selector": COMPOSER, "text": COMPOSER_AR, "want": "rtl"},
                ),
                (
                    "input_composer_latin",
                    input_direction,
                    {"selector": COMPOSER, "text": "hello", "want": "ltr"},
                ),
                ("mirror_on_dir_flip", mirror_on_dir_flip, {"selectors": [ME, THEM, AVATAR]}),
                ("no_physical_css", no_physical_css, {}),
                ("no_horizontal_overflow", no_horizontal_overflow, {}),
                ("card_fits", card_fits, {}),
                ("bundle_is_built_output", bundle_is_built_output, {}),
                ("index_html_static", static_index, {"root": root}),
                ("requests_allowed", requests_allowed, {}),
                ("toolchain_intact", toolchain_intact, {}),
            ],
        )
    ]


if __name__ == "__main__":
    results = grade(Path(sys.argv[1]), plan(Path(sys.argv[1]), Path(sys.argv[2])))
    print(json.dumps(results, sort_keys=True))
    sys.exit(0 if all(results.values()) else 1)
