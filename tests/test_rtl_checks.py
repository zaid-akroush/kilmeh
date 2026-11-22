"""Known-good / known-bad snippet tests for the RTL check library (needs Chromium)."""

import socket
import threading
from contextlib import contextmanager
from pathlib import Path

import pytest

from kilmeh.graders import rtl_checks as rc

pytestmark = pytest.mark.browser


def page_for(tmp_path: Path, html: str, **kwargs):
    (tmp_path / "index.html").write_text(html, encoding="utf-8")
    return rc.open_page(tmp_path, **kwargs)


def passes(result: rc.Result) -> bool:
    return result[0]


def test_open_page_aborts_external_requests(tmp_path):
    html = '<!doctype html><img id="x" src="https://example.com/x.png"><p id="ok">hi</p>'
    with page_for(tmp_path, html) as page:
        assert page.locator("#ok").inner_text() == "hi"
        assert page.evaluate("document.getElementById('x').naturalWidth") == 0
        assert page.kilmeh_aborted == ["https://example.com/x.png"]


def test_open_page_refuses_path_escape(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "index.html").write_text("<!doctype html><p>x</p>", encoding="utf-8")
    (tmp_path / "secret").write_text("top secret", encoding="utf-8")
    # the resolver itself: escapes (plain and encoded) and missing files give None
    assert rc.resolve_path(root, "/index.html") == (root / "index.html").resolve()
    assert rc.resolve_path(root, "/../secret") is None
    assert rc.resolve_path(root, "/%2e%2e/secret") is None
    assert rc.resolve_path(root, "/missing.txt") is None
    # and through the browser: a 404, not the file
    with rc.open_page(root) as page:
        assert page.evaluate("fetch('/%2e%2e/secret').then(r => r.status)") == 404
        assert page.evaluate("fetch('/missing.txt').then(r => r.status)") == 404


def test_open_page_override_serves_build_output(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "app.js").write_text("document.title = 'built'", encoding="utf-8")
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "app.js").write_text("document.title = 'stale'", encoding="utf-8")
    html = '<!doctype html><script src="/dist/app.js"></script>'
    with page_for(tmp_path, html, overrides={"/dist/app.js": out / "app.js"}) as page:
        assert page.title() == "built"


def test_root_dir_lang(tmp_path):
    good = '<!doctype html><html dir="rtl" lang="ar-JO"><body>x</body></html>'
    bad = '<!doctype html><html lang="ar"><body>x</body></html>'
    with page_for(tmp_path, good) as page:
        assert passes(rc.root_dir_lang(page))
    with page_for(tmp_path, bad) as page:
        assert not passes(rc.root_dir_lang(page))
    wrong_lang = '<!doctype html><html dir="rtl" lang="en"><body>x</body></html>'
    with page_for(tmp_path, wrong_lang) as page:
        assert not passes(rc.root_dir_lang(page))


def test_computed_direction(tmp_path):
    good = '<!doctype html><html dir="rtl"><body><main>x</main></body></html>'
    bad = (
        '<!doctype html><html dir="rtl"><style>body{direction:ltr}</style>'
        "<body><main>x</main></body></html>"
    )
    with page_for(tmp_path, good) as page:
        assert passes(rc.computed_direction(page, ["body", "main"]))
    with page_for(tmp_path, bad) as page:
        assert not passes(rc.computed_direction(page, ["body", "main"]))
        assert not passes(rc.computed_direction(page, ["#nope"]))


def test_no_horizontal_overflow(tmp_path):
    good = '<!doctype html><html dir="rtl"><body><p>fluid</p></body></html>'
    bad = (
        '<!doctype html><html dir="rtl"><style>body{margin:0}.wide{width:400px}</style>'
        '<body><div class="wide">wide</div></body></html>'
    )
    with page_for(tmp_path, good, width=360) as page:
        assert passes(rc.no_horizontal_overflow(page))
    with page_for(tmp_path, bad, width=360) as page:
        assert not passes(rc.no_horizontal_overflow(page))


def test_on_side(tmp_path):
    good = (
        '<!doctype html><html dir="rtl"><style>body{margin:0}header{display:flex}</style>'
        '<body><header><b id="logo">logo</b><i id="btn" style="margin-inline-start:auto">b</i>'
        "</header></body></html>"
    )
    bad = (
        '<!doctype html><html dir="rtl"><style>body{margin:0}#logo{float:left}</style>'
        '<body><b id="logo">logo</b></body></html>'
    )
    with page_for(tmp_path, good) as page:
        assert passes(rc.on_side(page, "#logo", "right"))
        assert passes(rc.on_side(page, "#btn", "left"))
        assert not passes(rc.on_side(page, "#logo", "left"))
        assert not passes(rc.on_side(page, "#nope", "left"))
    with page_for(tmp_path, bad) as page:
        assert not passes(rc.on_side(page, "#logo", "right"))


def test_order_rtl(tmp_path):
    good = (
        '<!doctype html><html dir="rtl"><nav style="display:flex;gap:8px">'
        "<a>1</a><a>2</a><a>3</a></nav></html>"
    )
    bad = (
        '<!doctype html><html dir="rtl"><nav style="display:flex;flex-direction:row-reverse;'
        'gap:8px"><a>1</a><a>2</a><a>3</a></nav></html>'
    )
    with page_for(tmp_path, good) as page:
        assert passes(rc.order_rtl(page, "nav a"))
        assert not passes(rc.order_rtl(page, "nav"))  # fewer than two matches
    with page_for(tmp_path, bad) as page:
        assert not passes(rc.order_rtl(page, "nav a"))


def test_mirror_on_dir_flip(tmp_path):
    good = (
        '<!doctype html><html dir="rtl"><style>body{margin:0}'
        "#a{margin-inline-start:40px;width:100px}</style><body><div id=a>x</div></body></html>"
    )
    bad = (
        '<!doctype html><html dir="rtl"><style>body{margin:0}'
        "#a{margin-left:40px;width:100px}</style><body><div id=a>x</div></body></html>"
    )
    with page_for(tmp_path, good) as page:
        assert passes(rc.mirror_on_dir_flip(page, ["#a"]))
        assert page.evaluate("document.documentElement.dir") == "rtl"  # restored
        assert not passes(rc.mirror_on_dir_flip(page, ["#nope"]))
    with page_for(tmp_path, bad) as page:
        assert not passes(rc.mirror_on_dir_flip(page, ["#a"]))


def test_no_physical_css(tmp_path):
    good = (
        '<!doctype html><html dir="rtl"><style>'
        "body{margin:0 auto;text-align:start}.a{margin-inline-start:1rem;padding:0 4px}"
        ".b{border-inline-start:2px solid;border-radius:4px}"
        "@media (max-width:600px){.a{padding-inline-end:2px}}"
        '</style><body><div class="a">x</div></body></html>'
    )
    bad = (
        '<!doctype html><html dir="rtl"><style>.a{margin-left:1rem}</style>'
        '<body><div class="a">x</div></body></html>'
    )
    with page_for(tmp_path, good) as page:
        assert passes(rc.no_physical_css(page)), rc.no_physical_css(page)
    with page_for(tmp_path, bad) as page:
        ok, detail = rc.no_physical_css(page)
        assert not ok and ".a" in detail and "margin-left" in detail
    for rule in (
        ".a{text-align:left}",
        ".a{float:right}",
        ".a{clear:left}",
        ".a{margin:0 0 0 1rem}",
        ".a{left:0}",
        ".a{border-left:1px solid}",
        ".a{border-top-left-radius:4px}",
        "@media (min-width:1px){.a{padding-right:3px}}",
    ):
        html = f'<!doctype html><html dir="rtl"><style>{rule}</style><body><i class="a">x</i>'
        with page_for(tmp_path, html) as page:
            assert not passes(rc.no_physical_css(page)), rule


def test_no_physical_css_inline_style(tmp_path):
    good = '<!doctype html><html dir="rtl"><body><div style="padding-inline-end:8px">x</div>'
    bad = '<!doctype html><html dir="rtl"><body><div style="padding-right:8px">x</div>'
    with page_for(tmp_path, good) as page:
        assert passes(rc.no_physical_css(page))
    with page_for(tmp_path, bad) as page:
        assert not passes(rc.no_physical_css(page))


def test_no_physical_css_allow_list(tmp_path):
    bad = (
        '<!doctype html><html dir="rtl"><style>.legacy{margin-left:1rem}</style>'
        '<body><div class="legacy">x</div></body></html>'
    )
    with page_for(tmp_path, bad) as page:
        assert not passes(rc.no_physical_css(page))
        assert passes(rc.no_physical_css(page, allow=[".legacy"]))
        assert not passes(rc.no_physical_css(page, allow=[".other"]))


def test_no_physical_tailwind(tmp_path):
    good = (
        '<!doctype html><html dir="rtl"><body><div class="ms-4 ps-2 text-start md:ms-2">x</div>'
        '<svg class="icon"></svg></body></html>'
    )
    bad = '<!doctype html><html dir="rtl"><body><div class="flex ml-4">x</div></body></html>'
    with page_for(tmp_path, good) as page:
        assert passes(rc.no_physical_tailwind(page))
    with page_for(tmp_path, bad) as page:
        ok, detail = rc.no_physical_tailwind(page)
        assert not ok and "ml-4" in detail


def test_icon_points(tmp_path):
    svg = (
        '<svg id="fwd" class="fwd" width="20" height="20" viewBox="0 0 20 20">'
        '<line x1="2" y1="10" x2="14" y2="10" stroke="black"/>'
        '<g data-part="head"><polyline points="12,4 18,10 12,16" fill="none" stroke="black"/></g>'
        "</svg>"
    )
    good = (
        '<!doctype html><html dir="rtl"><style>[dir=rtl] .fwd{transform:scaleX(-1)}</style>'
        f"<body>{svg}</body></html>"
    )
    bad = f'<!doctype html><html dir="rtl"><body>{svg}</body></html>'
    with page_for(tmp_path, good) as page:
        assert passes(rc.icon_points(page, "#fwd", "[data-part=head]", "left"))
        assert not passes(rc.icon_points(page, "#fwd", "[data-part=head]", "right"))
        assert not passes(rc.icon_points(page, "#nope", "[data-part=head]", "left"))
        assert not passes(rc.icon_points(page, "#fwd", "[data-part=nope]", "left"))
    with page_for(tmp_path, bad) as page:
        assert not passes(rc.icon_points(page, "#fwd", "[data-part=head]", "left"))
        assert passes(rc.icon_points(page, "#fwd", "[data-part=head]", "right"))


def test_bidi_isolated(tmp_path):
    good = (
        '<!doctype html><html dir="rtl"><body><p><bdi id="a">INV-0042</bdi></p>'
        '<p><span id="b" dir="ltr">+962 7 9123 4567</span></p>'
        '<p><span id="c" style="unicode-bidi:plaintext">x</span></p></body></html>'
    )
    bad = '<!doctype html><html dir="rtl"><body><p><span id="a">INV-0042</span></p></body></html>'
    with page_for(tmp_path, good) as page:
        assert passes(rc.bidi_isolated(page, ["#a", "#b", "#c"]))
        assert not passes(rc.bidi_isolated(page, ["#nope"]))
    with page_for(tmp_path, bad) as page:
        assert not passes(rc.bidi_isolated(page, ["#a"]))


def test_input_direction(tmp_path):
    good = '<!doctype html><html dir="rtl"><body><input id="e" type="email" dir="ltr">'
    bad = '<!doctype html><html dir="rtl"><body><input id="e" type="email">'
    with page_for(tmp_path, good) as page:
        assert passes(rc.input_direction(page, "#e", "a@b.co", "ltr"))
        assert not passes(rc.input_direction(page, "#e", "a@b.co", "rtl"))
        assert not passes(rc.input_direction(page, "#nope", "a@b.co", "ltr"))
    with page_for(tmp_path, bad) as page:
        assert not passes(rc.input_direction(page, "#e", "a@b.co", "ltr"))


def arabic_sample() -> str:
    """Arabic bytes copied from an existing fixture (the farewell task's README title)."""
    readme = Path(__file__).resolve().parent.parent / (
        "tasks/b-arabic-in-code/arabic-in-code-farewell/fixture/README.md"
    )
    sample = readme.read_text(encoding="utf-8").splitlines()[0].lstrip("# ")
    assert any("؀" <= ch <= "ۿ" for ch in sample)
    return sample


def test_input_direction_auto(tmp_path):
    good = '<!doctype html><html dir="ltr"><body><input id="n" dir="auto">'
    bad = '<!doctype html><html dir="ltr"><body><input id="n" dir="ltr">'
    sample = arabic_sample()
    with page_for(tmp_path, good) as page:
        result = rc.input_direction(page, "#n", sample, "rtl")
        assert passes(result), result
        assert passes(rc.input_direction(page, "#n", "Sara", "ltr"))
    with page_for(tmp_path, bad) as page:
        assert not passes(rc.input_direction(page, "#n", sample, "rtl"))


def test_grade_isolates_exceptions(tmp_path):
    (tmp_path / "index.html").write_text(
        '<!doctype html><html dir="rtl" lang="ar"><body>x</body></html>', encoding="utf-8"
    )

    def boom(page):
        raise RuntimeError("kaboom")

    plan = [
        ({}, [("dir", rc.root_dir_lang, {}), ("boom", boom, {})]),
        ({"width": 360}, [("overflow", rc.no_horizontal_overflow, {})]),
    ]
    assert rc.grade(tmp_path, plan) == {"dir": True, "boom": False, "overflow": True}
    with pytest.raises(ValueError, match="duplicate"):
        rc.grade(tmp_path, [({}, [("k", rc.root_dir_lang, {})]), ({}, [("k", boom, {})])])
    # a page that cannot open fails every check in its group, and the rest still run
    plan = [
        ({"path": "/nope.html"}, [("a", rc.root_dir_lang, {})]),
        ({}, [("b", rc.root_dir_lang, {})]),
    ]
    result = rc.grade(tmp_path, plan)
    assert result["a"] is False and result["b"] is True


def test_grade_raising_check_does_not_taint_neighbours(tmp_path):
    (tmp_path / "index.html").write_text(
        '<!doctype html><html dir="rtl" lang="ar"><body><p id="p">x</p></body></html>',
        encoding="utf-8",
    )

    def boom(page):
        raise RuntimeError("kaboom")

    group = [
        ("first", boom, {}),
        ("dir", rc.root_dir_lang, {}),
        ("computed", rc.computed_direction, {"selectors": ["#p"]}),
        ("wrong", rc.computed_direction, {"selectors": ["#p"], "want": "ltr"}),
        ("last", rc.no_horizontal_overflow, {}),
    ]
    assert rc.grade(tmp_path, [({}, group)]) == {
        "first": False,
        "dir": True,
        "computed": True,
        "wrong": False,
        "last": True,
    }


# ---- review fixes: network, visibility, overflow, CSS coverage, mutants ----


@contextmanager
def tcp_listener():
    """A real local listener; records every connection it gets."""
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen()
    server.settimeout(0.2)
    hits: list[int] = []
    stop = threading.Event()

    def run():
        while not stop.is_set():
            try:
                conn, _ = server.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            hits.append(1)
            conn.close()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    try:
        yield server.getsockname()[1], hits
    finally:
        stop.set()
        thread.join()
        server.close()


def test_open_page_blocks_every_network_path(tmp_path):
    probe = """async (port) => {
      const base = `127.0.0.1:${port}`;
      try { await fetch(`http://${base}/f`, {mode: 'no-cors'}); } catch (e) {}
      try { navigator.sendBeacon(`http://${base}/b`, 'x'); } catch (e) {}
      new Image().src = `http://${base}/i`;
      try { new WebSocket(`ws://${base}/w`); } catch (e) {}
      try { new WebSocket('ws://kilmeh.local/w'); } catch (e) {}
      await new Promise(r => setTimeout(r, 800));
    }"""
    with tcp_listener() as (port, hits), page_for(tmp_path, "<!doctype html><p>x</p>") as page:
        page.evaluate(probe, port)
        aborted = list(page.kilmeh_aborted)
    assert hits == [], "a request reached the local listener"
    assert f"http://127.0.0.1:{port}/f" in aborted
    assert f"ws://127.0.0.1:{port}/w" in aborted


def test_launch_args_disable_dev_shm():
    assert "--disable-dev-shm-usage" in rc.launch_args()


def test_resolve_path_hostile_inputs(tmp_path):
    (tmp_path / "index.html").write_text("x", encoding="utf-8")
    assert rc.resolve_path(tmp_path, "/a%00b") is None
    assert rc.resolve_path(tmp_path, "/index.html%00.png") is None
    assert rc.resolve_path(tmp_path, "/o.js", {"/o.js": tmp_path / "gone.js"}) is None
    assert rc.resolve_path(tmp_path, "/o.js", {"/o.js": tmp_path / "index.html"}) is not None


def test_open_page_null_byte_and_missing_override_are_404_fast(tmp_path):
    with page_for(tmp_path, "<!doctype html><p>x</p>", overrides={"/o.js": tmp_path / "gone"}) as p:
        for url in ("/a%00b", "/o.js"):  # a hung request resolves to 'hang' after 3 s
            probe = (
                f"Promise.race([fetch('{url}').then(r => r.status),"
                " new Promise(r => setTimeout(() => r('hang'), 3000))])"
            )
            assert p.evaluate(probe) == 404, url


def test_root_dir_lang_rejects_dangling_subtag(tmp_path):
    html = '<!doctype html><html dir="rtl" lang="ar-"><body>x</body></html>'
    with page_for(tmp_path, html) as page:
        assert not passes(rc.root_dir_lang(page))


def test_mirror_on_dir_flip_tolerance(tmp_path):
    def html(shift):
        return (
            '<!doctype html><html dir="rtl"><style>body{margin:0}'
            f"#a{{margin-inline-start:40px;width:100px;position:relative;left:{shift}px}}"
            "</style><body><div id=a>x</div></body></html>"
        )

    # a relative offset moves the box the same way in both directions: mirror error = 2 * shift
    with page_for(tmp_path, html(0.5)) as page:  # 1px off: inside the 2px tolerance
        assert passes(rc.mirror_on_dir_flip(page, ["#a"]))
    with page_for(tmp_path, html(1.5)) as page:  # 3px off: outside it
        assert not passes(rc.mirror_on_dir_flip(page, ["#a"]))


def test_mirror_on_dir_flip_symmetric_box_is_vacuous(tmp_path):
    """Known limit (documented in the docstring): a centred box passes any layout."""
    html = (
        '<!doctype html><html dir="rtl"><style>body{margin:0}'
        "#a{margin:0 auto;width:100px}</style><body><div id=a>x</div></body></html>"
    )
    with page_for(tmp_path, html) as page:
        assert passes(rc.mirror_on_dir_flip(page, ["#a"]))


HIDERS = [
    "display:none",
    "visibility:hidden",
    "opacity:0",
    "width:0;height:0;padding:0",
    "position:absolute;left:5000px",
]


@pytest.mark.parametrize("hide", HIDERS)
def test_on_side_requires_a_visible_element_in_view(tmp_path, hide):
    html = (
        '<!doctype html><html dir="rtl"><style>body{margin:0}</style><body>'
        f'<b id="x" style="display:block;width:50px;height:20px;margin-inline-start:0;{hide}">x'
        "</b></body></html>"
    )
    with page_for(tmp_path, html) as page:
        assert not passes(rc.on_side(page, "#x", "right"))
        assert not passes(rc.on_side(page, "#x", "left"))


def test_on_side_hidden_by_parent(tmp_path):
    html = (
        '<!doctype html><html dir="rtl"><body><div style="opacity:0"><b id="x">x</b></div>'
        "</body></html>"
    )
    with page_for(tmp_path, html) as page:
        assert not passes(rc.on_side(page, "#x", "right"))


@pytest.mark.parametrize("hide", HIDERS)
def test_order_rtl_fails_if_any_item_is_invisible(tmp_path, hide):
    html = (
        '<!doctype html><html dir="rtl"><nav style="display:flex;gap:8px">'
        f'<a>1</a><a style="{hide}">2</a><a>3</a></nav></html>'
    )
    with page_for(tmp_path, html) as page:
        assert not passes(rc.order_rtl(page, "nav a"))


def test_no_horizontal_overflow_geometry_pass(tmp_path):
    def doc(css, body):
        return f'<!doctype html><html dir="rtl"><style>{css}</style><body>{body}</body></html>'

    wide = '<div class="w">wide</div>'
    cases = {
        "overflow-x hidden on html and body": doc(
            "html,body{overflow-x:hidden;margin:0}.w{width:900px}", wide
        ),
        "position fixed": doc("body{margin:0}.w{position:fixed;top:0;left:0;width:900px}", wide),
        "clipped off the left edge": doc(
            "html,body{overflow-x:hidden;margin:0}.w{position:absolute;top:0;left:-200px;"
            "width:100px;height:10px}",
            wide,
        ),
    }
    for name, html in cases.items():
        with page_for(tmp_path, html, width=360) as page:
            assert not passes(rc.no_horizontal_overflow(page)), name
    ok = doc(
        "body{margin:0}.scroller{overflow-x:auto}.w{width:900px}"
        ".sr{position:absolute;width:1px;height:1px;clip:rect(0 0 0 0)}",
        f'<div class="scroller">{wide}</div><span class="sr">skip</span>'
        '<div style="display:none;width:900px">h</div>',
    )
    with page_for(tmp_path, ok, width=360) as page:
        assert passes(rc.no_horizontal_overflow(page)), rc.no_horizontal_overflow(page)


def test_no_physical_css_import_shadow_adopted(tmp_path):
    (tmp_path / "a.css").write_text(".a{margin-left:1rem}", encoding="utf-8")
    head = '<!doctype html><html dir="rtl"><body><i class="a">x</i><div id="h"></div>'
    cases = {
        "@import": '<!doctype html><html dir="rtl"><style>@import "/a.css";</style>'
        '<body><i class="a">x</i></body></html>',
        "shadow style": head + "<script>document.getElementById('h').attachShadow({mode:'open'})"
        ".innerHTML='<style>.a{margin-left:1px}</style><i class=a>y</i>'</script>",
        "shadow inline": head + "<script>document.getElementById('h').attachShadow({mode:'open'})"
        ".innerHTML='<div style=\"padding-right:8px\">y</div>'</script>",
        "adopted": head
        + "<script>const s=new CSSStyleSheet();s.replaceSync('.a{margin-left:1px}');"
        "document.adoptedStyleSheets=[s]</script>",
        "adopted in shadow": head + "<script>const r=document.getElementById('h')"
        ".attachShadow({mode:'open'});const s=new CSSStyleSheet();"
        "s.replaceSync('.a{margin-left:1px}');r.adoptedStyleSheets=[s]</script>",
    }
    for name, html in cases.items():
        with page_for(tmp_path, html) as page:
            assert not passes(rc.no_physical_css(page)), name


def test_no_physical_css_more_properties(tmp_path):
    for rule in (
        ".a{text-align:-webkit-left}",
        ".a{text-align:-webkit-right}",
        ".a{text-align-last:left}",
        ".a{scroll-margin-left:4px}",
        ".a{scroll-padding-right:4px}",
        ".a{border-left-color:red}",
        ".a{border-right-style:solid}",
        ".a{margin-left:1px;margin-right:2px}",
    ):
        html = f'<!doctype html><html dir="rtl"><style>{rule}</style><body><i class="a">x</i>'
        with page_for(tmp_path, html) as page:
            assert not passes(rc.no_physical_css(page)), rule


def test_no_physical_css_computed_pass_catches_var(tmp_path):
    bad = (
        '<!doctype html><html dir="rtl"><style>:root{--s:left}.a{text-align:var(--s);'
        'float:var(--s)}</style><body><div class="a">x</div></body></html>'
    )
    hidden = bad.replace('class="a"', 'class="a" style="display:none"')
    with page_for(tmp_path, bad) as page:
        ok, detail = rc.no_physical_css(page)
        assert not ok and "computed" in detail
        assert passes(rc.no_physical_css(page, allow=[".a"]))
    with page_for(tmp_path, hidden) as page:  # only visible elements are inspected
        assert passes(rc.no_physical_css(page))


def test_no_physical_css_zero_values_and_selector_lists(tmp_path):
    good = (
        '<!doctype html><html dir="rtl"><style>.a{margin-left:0;padding-left:0px;'
        "border-left-width:0}.b{margin-right:0}</style><body><i class=a>x</i></body></html>"
    )
    with page_for(tmp_path, good) as page:
        assert passes(rc.no_physical_css(page)), rc.no_physical_css(page)
    bad = '<!doctype html><html dir="rtl"><style>.a{margin-left:0;margin-right:1px}</style><body>'
    with page_for(tmp_path, bad) as page:
        assert not passes(rc.no_physical_css(page))
    listed = (
        '<!doctype html><html dir="rtl"><style>.a, .b{margin-left:1rem}</style>'
        "<body><i class=a>x</i></body></html>"
    )
    with page_for(tmp_path, listed) as page:
        assert not passes(rc.no_physical_css(page))
        assert passes(rc.no_physical_css(page, allow=[".a"]))
        assert passes(rc.no_physical_css(page, allow=[".b"]))
    left_zero = '<!doctype html><html dir="rtl"><style>.a{position:absolute;left:0}</style><body>'
    with page_for(tmp_path, left_zero) as page:  # left:0 alone pins the box to the left edge
        assert not passes(rc.no_physical_css(page))


def test_no_physical_css_scope_decision_keyframes_and_background(tmp_path):
    """Decision, documented in the docstring: @keyframes and background-position are not graded."""
    html = (
        '<!doctype html><html dir="rtl"><style>@keyframes k{from{margin-left:0}to{margin-left:9px}}'
        ".a{background-position:left top}</style><body><i class=a>x</i></body></html>"
    )
    with page_for(tmp_path, html) as page:
        assert passes(rc.no_physical_css(page))


def test_no_physical_tailwind_arbitrary_property_and_false_fails(tmp_path):
    html = '<!doctype html><html dir="rtl"><body><div class="{c}">x</div></body></html>'
    for cls in ("[margin-left:4px]", "md:[padding-right:2px]", "[float:left]"):
        with page_for(tmp_path, html.replace("{c}", cls)) as page:
            assert not passes(rc.no_physical_tailwind(page)), cls
    for cls in (
        "left-nav right-column pr-card border-l-accent",
        "ltr:ml-4",
        "space-x-4 [color:red]",
    ):
        with page_for(tmp_path, html.replace("{c}", cls)) as page:
            assert passes(rc.no_physical_tailwind(page)), cls


# ---- QA fairness fixes (PR B): input_direction, bidi_isolated, fits_width ----


def test_input_direction_accepts_css_direction_and_plaintext(tmp_path):
    ar = arabic_sample()
    css_ltr = (
        '<!doctype html><html dir="rtl"><style>#e{direction:ltr}</style><body>'
        '<input id="e" type="email">'
    )
    plain = (
        '<!doctype html><html dir="rtl"><style>#n{unicode-bidi:plaintext}</style><body>'
        '<input id="n">'
    )
    with page_for(tmp_path, css_ltr) as page:  # CSS direction, no dir attribute
        assert passes(rc.input_direction(page, "#e", "a@b.co", "ltr"))
        assert not passes(rc.input_direction(page, "#e", "a@b.co", "rtl"))
    with page_for(tmp_path, plain) as page:  # the typed text decides
        assert passes(rc.input_direction(page, "#n", ar, "rtl"))
        assert passes(rc.input_direction(page, "#n", "Sara", "ltr"))
        assert not passes(rc.input_direction(page, "#n", ar, "ltr"))
        assert not passes(rc.input_direction(page, "#n", "Sara", "rtl"))
    # still bad: inheriting rtl with nothing else, and a forced direction against the text
    inherit = '<!doctype html><html dir="rtl"><body><input id="n">'
    with page_for(tmp_path, inherit) as page:
        assert not passes(rc.input_direction(page, "#n", "a@b.co", "ltr"))


def test_bidi_isolated_nested_isolate_controls_and_embed(tmp_path):
    def doc(inner, css=""):
        return f'<!doctype html><html dir="rtl"><style>{css}</style><body><p>{inner}</p>'

    good = {
        "nested bdi": '<span id="a"><bdi>INV-0042</bdi></span>',
        "nested dir attribute": '<span id="a"><span dir="ltr">INV-0042</span></span>',
        "nested isolate css": '<span id="a"><i style="unicode-bidi:isolate">INV-0042</i></span>',
        "LRI": '<span id="a">⁦INV-0042⁩</span>',
        "RLI": '<span id="a">⁧INV-0042⁩</span>',
        "FSI": '<span id="a">⁨INV-0042⁩</span>',
        "FSI with spaces around": '<span id="a"> ⁨INV-0042⁩ </span>',
    }
    for name, inner in good.items():
        with page_for(tmp_path, doc(inner)) as page:
            assert passes(rc.bidi_isolated(page, ["#a"])), name
    bad = {
        "embed": ('<span id="a">INV-0042</span>', "#a{unicode-bidi:embed}"),
        "text partly outside the isolate": ('<span id="a">x <bdi>INV</bdi> y</span>', ""),
        "opener without PDI": ('<span id="a">⁦INV-0042</span>', ""),
        "plain span": ('<span id="a">INV-0042</span>', ""),
    }
    for name, (inner, css) in bad.items():
        with page_for(tmp_path, doc(inner, css)) as page:
            assert not passes(rc.bidi_isolated(page, ["#a"])), name


def test_fits_width(tmp_path):
    def doc(css, body):
        return f'<!doctype html><html dir="rtl"><style>{css}</style><body>{body}</body></html>'

    table = '<table id="t"><tr><td>x</td></tr></table>'
    good = doc("body{margin:0}table{width:100%}", table)
    wide = doc("body{margin:0}table{width:420px}", table)
    clipped = doc(
        "body{margin:0}main{overflow-x:hidden}table{width:420px}", f"<main>{table}</main>"
    )
    inside_clip = doc(
        "body{margin:0}main{overflow-x:hidden;margin:0 100px}table{width:300px}",
        f"<main>{table}</main>",
    )
    with page_for(tmp_path, good, width=360) as page:
        assert passes(rc.fits_width(page, "#t"))
        assert not passes(rc.fits_width(page, "#nope"))
    with page_for(tmp_path, wide, width=360) as page:
        assert not passes(rc.fits_width(page, "#t"))
    with page_for(tmp_path, clipped, width=360) as page:  # hidden by an ancestor
        assert not passes(rc.fits_width(page, "#t"))
    with page_for(tmp_path, inside_clip, width=360) as page:  # clipped inside the viewport
        assert not passes(rc.fits_width(page, "#t"))
    hidden = doc("body{margin:0}", '<table id="t" style="display:none"><tr><td>x</td></tr></table>')
    with page_for(tmp_path, hidden, width=360) as page:
        assert not passes(rc.fits_width(page, "#t"))


def test_visual_order(tmp_path):
    ar = arabic_sample().split()[0]

    def doc(body, css=""):
        return f'<!doctype html><html dir="rtl"><style>{css}</style><body>{body}</body></html>'

    rtl = f'<p id="p">{ar} Ali {ar} Omar</p>'  # rtl base: Ali sits right of Omar
    with page_for(tmp_path, doc(rtl)) as page:
        assert passes(rc.visual_order(page, "#p", ["Ali", "Omar"], "rtl"))
        assert not passes(rc.visual_order(page, "#p", ["Ali", "Omar"], "ltr"))
        assert not passes(rc.visual_order(page, "#p", ["Omar", "Ali"], "ltr"))  # typed order
        assert not passes(rc.visual_order(page, "#p", ["Sam", "Ali"], "rtl"))
        assert not passes(rc.visual_order(page, "#nope", ["Ali", "Omar"], "rtl"))
        with pytest.raises(ValueError):
            rc.visual_order(page, "#p", ["Ali"], "rtl")
        with pytest.raises(ValueError):
            rc.visual_order(page, "#p", ["Ali", "Omar"], "up")
    with page_for(tmp_path, doc(f'<p id="p" dir="auto">Hi {ar} Omar</p>')) as page:
        assert passes(rc.visual_order(page, "#p", ["Hi", "Omar"], "ltr"))
    forced = doc(rtl, "#p{direction:ltr;unicode-bidi:bidi-override}")
    with page_for(tmp_path, forced) as page:
        assert not passes(rc.visual_order(page, "#p", ["Ali", "Omar"], "rtl"))
    # mirrored, hidden, covered or wrapped onto two lines: never a pass
    for css in (
        "#p{direction:ltr;unicode-bidi:bidi-override;transform:scaleX(-1)}",
        "#p{direction:ltr;unicode-bidi:bidi-override;display:inline-block;scale:-1 1}",
        "#p{visibility:hidden}",
        "#p{opacity:0}",
        "body{position:relative}body::after{content:'';position:absolute;inset:0;background:#fff}",
        "#p{width:1px}",
    ):
        with page_for(tmp_path, doc(rtl, css)) as page:
            assert not passes(rc.visual_order(page, "#p", ["Ali", "Omar"], "rtl")), css


def test_visual_order_rejects_reversed_letters(tmp_path):
    ar = arabic_sample().split()[0]
    assert len(ar) > 1
    body = f'<p id="p">{ar} <span id="n">Ali</span> {ar} Omar</p>'
    good = f'<!doctype html><html dir="rtl"><body>{body}</body></html>'
    # forced right to left inside the run: the run order still looks right, the letters do not
    flipped = good.replace(
        "<body>", "<style>#n{direction:rtl;unicode-bidi:isolate-override}</style><body>"
    )
    with page_for(tmp_path, good) as page:
        assert passes(rc.visual_order(page, "#p", ["Ali", "Omar"], "rtl"))
        assert passes(rc.visual_order(page, "#p", [ar, "Ali"], "rtl"))  # Arabic letters rtl
    with page_for(tmp_path, flipped) as page:
        assert not passes(rc.visual_order(page, "#p", ["Ali", "Omar"], "rtl"))
    forced = good.replace(
        "<body>", "<style>#p{direction:ltr;unicode-bidi:bidi-override}</style><body>"
    )
    with page_for(tmp_path, forced) as page:  # Arabic shown left to right: reversed letters
        assert not passes(rc.visual_order(page, "#p", [ar, "Ali"], "ltr"))


def test_visual_order_rejects_vertical_flips(tmp_path):
    ar = arabic_sample().split()[0]
    for css in (
        "#p{transform:scaleY(-1)}",
        "#p{transform:rotate(180deg)}",
        "#p{display:inline-block;scale:1 -1}",
        "#p{display:inline-block;rotate:180deg}",
    ):
        html = (
            f'<!doctype html><html dir="rtl"><style>{css}</style><body>'
            f'<p id="p">{ar} Ali {ar} Omar</p></body></html>'
        )
        with page_for(tmp_path, html) as page:
            assert not passes(rc.visual_order(page, "#p", ["Ali", "Omar"], "rtl")), css


def test_visual_order_rotate_property_alone(tmp_path):
    """Only the `rotate` branch catches this: single-character tokens skip the letter guard,
    the computed transform stays none, and a half turn makes the rtl run look ltr."""
    ar = arabic_sample().split()[0]
    body = f'<p id="p">{ar} 5 {ar} 3</p>'
    plain = f'<!doctype html><html dir="rtl"><body>{body}</body></html>'
    turned = plain.replace("<body>", "<style>#p{display:inline-block;rotate:180deg}</style><body>")
    with page_for(tmp_path, plain) as page:
        assert passes(rc.visual_order(page, "#p", ["5", "3"], "rtl"))
    with page_for(tmp_path, turned) as page:
        assert not passes(rc.visual_order(page, "#p", ["5", "3"], "ltr"))


def test_testid_texts_and_visible_text():
    html = (
        '<ul><li data-testid="a">Hi <b data-testid="b">Ali</b>\n  there<br><!-- note --></li></ul>'
    )
    assert rc.testid_texts(html) == {"a": "HiAlithere", "b": "Ali"}
    assert rc.visible_text("\u2068Ali\u2069 \u200e x\u200f ") == "Alix"
    assert rc.visible_text("Ali x") != rc.visible_text("x Ali")  # reordering still differs
    assert rc.visible_text("Ali\u200bx") != "Alix"  # only the listed marks are dropped


def test_text_kept(tmp_path):
    base = '<!doctype html><html dir="rtl"><body><p data-testid="a">{}</p></body></html>'
    want = {"a": "Hi Ali"}
    with page_for(tmp_path, base.format("Hi <bdi>\u2068Ali\u2069</bdi>")) as page:
        assert passes(rc.text_kept(page, want))
        assert not passes(rc.text_kept(page, {"nope": "x"}))
    with page_for(tmp_path, base.format("\n  Hi\n  <bdi>Ali</bdi>\n")) as page:  # reformatted
        assert passes(rc.text_kept(page, want))
    with page_for(tmp_path, base.format("Ali Hi")) as page:
        assert not passes(rc.text_kept(page, want))
