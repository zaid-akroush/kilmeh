"""In-image tests of the RTL tasks: reference passes, known-bad and untouched fail the exact
expected checks, and each check fails alone under its own mutation.

Needs Docker (marker `docker`): `uv run pytest -m docker tests/test_rtl_tasks.py`.
One container per task runs every case on a fresh copy of the fixture, with the network off.
"""

import functools
import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

from kilmeh import selftest

pytestmark = pytest.mark.docker

ROOT = Path(__file__).resolve().parent.parent
MUTATIONS = ROOT / "tests" / "rtl_mutations"
ALTERNATIVES = (
    ROOT / "tests" / "rtl_alternatives"
)  # correct solutions that differ from the reference
GAMING = ROOT / "tests" / "rtl_gaming"  # cheats applied on top of the reference; none may score 1
BUILD_TIMEOUT = 600
RUN_TIMEOUT = 900

# Every check key of each task's PLAN (one mutation script per key).
CHECKS = {
    "rtl-nav-fix": [
        "root_dir_lang",
        "computed_direction",
        "on_side_logo",
        "on_side_signin",
        "order_rtl_nav",
        "mirror_on_dir_flip",
        "no_physical_css",
        "no_horizontal_overflow_360",
    ],
    "rtl-order-summary-fix": [
        "root_dir_lang",
        "icon_next",
        "icon_back",
        "icon_logo",
        "icon_play",
        "bidi_isolated",
        "input_email",
        "input_phone",
        "input_name_ar",
        "input_name_latin",
        "no_horizontal_overflow",
        "table_fits",
        "svg_markup_unchanged",
    ],
    "rtl-react-chat": [
        "root_dir_lang",
        "bubbles_me_left",
        "bubbles_them_right",
        "avatar_at_start",
        "bidi_isolated",
        "input_composer_ar",
        "input_composer_latin",
        "mirror_on_dir_flip",
        "no_physical_css",
        "no_horizontal_overflow",
        "card_fits",
        "bundle_is_built_output",
        "index_html_static",
        "requests_allowed",
        "toolchain_intact",
    ],
    "rtl-tailwind-sidebar": [
        "root_dir_lang",
        "on_side_aside",
        "main_beside_sidebar",
        "mirror_on_dir_flip",
        "no_physical_tailwind",
        "testids_kept",
        "css_from_build",
        "no_physical_css",
        "no_horizontal_overflow_360",
    ],
    "rtl-contact-page-build": [
        "root_dir_lang",
        "computed_direction",
        "on_side_logo",
        "order_rtl_nav",
        "icon_next",
        "bidi_phone",
        "bidi_email",
        "input_name_ar",
        "input_name_latin",
        "input_email",
        "input_phone",
        "no_physical_css",
        "arabic_text",
        "svg_markup_unchanged",
        "elements_fit_1280",
        "no_shrink_tricks",
        "no_horizontal_overflow_360",
        "elements_fit_360",
        "static_page",
        "no_overlays_1280",
        "no_effects_1280",
        "readable_contrast_1280",
        "no_overlays_360",
        "no_effects_360",
        "readable_contrast_360",
    ],
    "rtl-bidi-chat-feed": [
        "root_dir_lang",
        "feed_rtl",
        "text_kept",
        "order_m1",
        "order_m2",
        "order_m3",
        "order_m4",
        "order_m5",
    ],
    "rtl-bidi-name-slots": [
        "root_dir_lang",
        "bidi_isolated",
        "order_n1",
        "order_n2",
        "order_n3",
        "order_n4",
        "text_kept",
    ],
    "rtl-bidi-data-cells": [
        "root_dir_lang",
        "cells_rtl",
        "text_kept",
        "order_path",
        "order_version",
        "order_phone",
        "order_code",
        "arabic_lead_right",
    ],
}

# rtl-tailwind-logical-convert grades three pages; each check key is prefixed by its page.
LC = "rtl-tailwind-logical-convert"
LC_PAGES = ("index", "notifications", "billing")
LC_CHECKS = [
    "root_dir_lang",
    "islands_direction",
    "ltr_islands_kept",
    "rtl_mirrors_ltr",
    "no_physical_tailwind",
    "testids_and_text_kept",
    "ltr_layout_unchanged",
    "ltr_styles_unchanged",
    "css_from_build",
    "no_physical_css",
    "no_horizontal_overflow_360",
]
CHECKS[LC] = [f"{page}.{check}" for page in LC_PAGES for check in LC_CHECKS]


def lc(checks, pages=LC_PAGES):
    """`<page>.<check>` keys for every page in pages."""
    return {f"{page}.{check}" for page in pages for check in checks}


# Observed with the reference grader; exact sets, so a new false pass or fail is noticed.
KNOWN_BAD_FAILS = {
    "rtl-nav-fix": {
        "root_dir_lang",
        "on_side_signin",
        "order_rtl_nav",
        "mirror_on_dir_flip",
        "no_physical_css",
    },
    "rtl-order-summary-fix": {
        "icon_logo",
        "icon_play",
        "bidi_isolated",
        "input_name_ar",
        "no_horizontal_overflow",
        "table_fits",
    },
    "rtl-react-chat": {
        "bubbles_me_left",
        "avatar_at_start",
        "bidi_isolated",
        "input_composer_latin",
        "mirror_on_dir_flip",
        "no_physical_css",
        "no_horizontal_overflow",
        "card_fits",
    },
    "rtl-tailwind-sidebar": {
        "mirror_on_dir_flip",
        "no_physical_css",
        "no_physical_tailwind",
    },
    "rtl-contact-page-build": {
        "bidi_email",
        "bidi_phone",
        "icon_next",
        "input_email",
        "input_name_latin",
        "input_phone",
        "no_physical_css",
        "root_dir_lang",
    },
    # every message forced right to left: the English-first and link-first ones break
    "rtl-bidi-chat-feed": {"order_m2", "order_m3"},
    # isolated but left right to left: the punctuation of Latin values still jumps
    "rtl-bidi-name-slots": {"order_n2", "order_n3"},
    # the whole value column left to right: Arabic moves left, phone groups stay reversed
    "rtl-bidi-data-cells": {"cells_rtl", "order_phone", "arabic_lead_right"},
    # billing.html is skipped by the regex pass, but its islands are flipped too and its text-left
    # still pins the IBAN text to the left
    LC: lc(
        [
            "islands_direction",
            "ltr_islands_kept",
            "rtl_mirrors_ltr",
            "no_physical_tailwind",
            "ltr_styles_unchanged",
            "no_physical_css",
        ],
        ["index", "notifications"],
    )
    | lc(
        ["islands_direction", "rtl_mirrors_ltr", "no_physical_tailwind", "no_physical_css"],
        ["billing"],
    ),
}
UNTOUCHED_FAILS = {
    "rtl-nav-fix": {
        "root_dir_lang",
        "computed_direction",
        "on_side_logo",
        "on_side_signin",
        "order_rtl_nav",
        "mirror_on_dir_flip",
        "no_physical_css",
    },
    "rtl-order-summary-fix": {
        "icon_next",
        "icon_back",
        "bidi_isolated",
        "input_email",
        "input_phone",
        "input_name_latin",
        "no_horizontal_overflow",
        "table_fits",
    },
    "rtl-react-chat": {
        "root_dir_lang",
        "bubbles_me_left",
        "bubbles_them_right",
        "avatar_at_start",
        "bidi_isolated",
        "input_composer_ar",
        "mirror_on_dir_flip",
        "no_physical_css",
        "no_horizontal_overflow",
        "card_fits",
    },
    "rtl-tailwind-sidebar": {
        "root_dir_lang",
        "on_side_aside",
        "main_beside_sidebar",
        "mirror_on_dir_flip",
        "no_physical_css",
        "no_physical_tailwind",
    },
    "rtl-contact-page-build": {
        "arabic_text",
        "bidi_email",
        "bidi_phone",
        "computed_direction",
        "elements_fit_1280",
        "elements_fit_360",
        "icon_next",
        "input_email",
        "input_name_ar",
        "input_name_latin",
        "input_phone",
        "on_side_logo",
        "order_rtl_nav",
        "root_dir_lang",
        "svg_markup_unchanged",
    },
    LC: lc(["root_dir_lang", "rtl_mirrors_ltr", "no_physical_tailwind", "no_physical_css"]),
    "rtl-bidi-chat-feed": {"order_m1", "order_m2", "order_m3", "order_m4", "order_m5"},
    "rtl-bidi-name-slots": {"bidi_isolated", "order_n1", "order_n2", "order_n3"},
    "rtl-bidi-data-cells": {"order_path", "order_version", "order_phone", "order_code"},
}

# Gaming cases: the exact checks each cheat fails (reference solution plus the cheat; the
# `fresh_` cases start from the unchanged fixture).
GAMING_FAILS = {
    "rtl-bidi-chat-feed": {
        "fresh_mirror_messages": {"order_m1", "order_m2", "order_m3", "order_m4", "order_m5"},
        "fresh_override_rtl": {"order_m1", "order_m2", "order_m3", "order_m4", "order_m5"},
        "hide_message": {"order_m2"},
        "cover_message": {"order_m3"},
        "reversed_text": {"order_m1", "text_kept"},
        "fresh_known_bad_retyped": {"text_kept"},
        "flip_upside_down": {"order_m2"},
    },
    "rtl-bidi-name-slots": {
        "fresh_mirror_notes": {"order_n2", "order_n3"},
        "fresh_retyped_value": {
            "bidi_isolated",
            "order_n1",
            "order_n2",
            "order_n3",
            "text_kept",
        },
        "fresh_override_all_slots": {"order_n4"},
        "transparent_note": {"order_n1"},
        "override_name": {"order_n1"},
    },
    "rtl-bidi-data-cells": {
        "fresh_mirror_values": {"order_path", "order_version", "order_phone", "order_code"},
        "fresh_override_rtl": {
            "order_path",
            "order_version",
            "order_phone",
            "order_code",
            "text_kept",
        },
        "override_lead": {"arabic_lead_right"},
        "hide_phone": {"order_phone"},
    },
    "rtl-react-chat": {
        "hide_me_bubbles": {"bubbles_me_left"},
        "hide_avatars": {"avatar_at_start"},
        "shrink_card_transform": {"card_fits"},
        "shrink_card_zoom": {"card_fits"},
        "collapse_card": {"card_fits"},
        "hide_overflow_body": {"no_horizontal_overflow", "card_fits"},
        "rename_testids": {"bubbles_me_left", "mirror_on_dir_flip"},
        "prebuilt_elsewhere": {"bundle_is_built_output", "index_html_static", "requests_allowed"},
        # index.html allow-list and the request allow-list
        "html_template": {"index_html_static"},
        "html_svg_script": {"index_html_static"},
        "html_object_embed": {"index_html_static", "requests_allowed"},
        "html_meta_refresh": {"index_html_static"},
        "html_modulepreload": {"index_html_static", "requests_allowed"},
        "iframe_same_origin": {"index_html_static", "requests_allowed"},
        "hidden_fetch_eval": {"requests_allowed"},
        "fresh_iframe_srcdoc": {"index_html_static", "requests_allowed"},
        # build isolation: nothing outside src/ may reach the graded bundle
        "fresh_tsconfig_jsximport": set(UNTOUCHED_FAILS["rtl-react-chat"]),
        "fresh_package_json_browser": set(UNTOUCHED_FAILS["rtl-react-chat"]),
        # fresh_ cases start from the unchanged fixture
        "fresh_dist_edit": set(UNTOUCHED_FAILS["rtl-react-chat"]),
        "fresh_edit_dist_css": set(UNTOUCHED_FAILS["rtl-react-chat"]),
        "fresh_tamper_react": set(UNTOUCHED_FAILS["rtl-react-chat"]),
        "fresh_inline_script_removes_itself": {"index_html_static"},
        # html and css are fixed there, only Chat.jsx is not: the fake esbuild must not rescue it
        "fresh_esbuild_replaced": {
            "bubbles_me_left",
            "avatar_at_start",
            "bidi_isolated",
            "input_composer_latin",
            "mirror_on_dir_flip",
            "no_physical_css",
        },
    },
    "rtl-tailwind-sidebar": {
        "dist_only_edit": {"main_beside_sidebar"},
        "hide_sidebar": {
            "on_side_aside",
            "main_beside_sidebar",
            "mirror_on_dir_flip",
            "testids_kept",
        },
        "clip_overflow": {"no_horizontal_overflow_360"},
        "scale_down": {"main_beside_sidebar", "mirror_on_dir_flip"},
        "zoom_out": {"main_beside_sidebar"},
        "own_stylesheet": {"css_from_build"},
        "inline_style": {"css_from_build"},
        "delete_text": {"testids_kept"},
        # QA cases, run on the fresh fixture (no reference solution underneath).
        "fresh_handcss": {"no_physical_css"},
        "fresh_applycss": {"no_physical_css"},
        "fresh_dataimport": {"no_physical_css"},
        "fresh_ltrvariant": {"no_physical_css"},
        "fresh_insetshorthand": {"no_physical_css"},
    },
    "rtl-contact-page-build": {
        "clip_html_body": {"elements_fit_360", "no_horizontal_overflow_360"},
        "clip_in_scroller": {"elements_fit_360"},
        "hide_runs_on_phones": {"elements_fit_360"},
        "invisible_logo": {"arabic_text", "elements_fit_1280", "elements_fit_360", "on_side_logo"},
        "move_arrow_head": {"icon_next", "svg_markup_unchanged"},
        "scale_body": {"no_shrink_tricks"},
        "tiny_text": {"no_shrink_tricks"},
        "zoom_page": {"no_shrink_tricks"},
        # fresh_ cases start from the unchanged fixture: planted look-alike grader files
        # must change nothing
        # QA's cases (each starts from the unchanged fixture)
        "fresh_qa_a01_english_contact_text": {"arabic_text"},
        "fresh_qa_a10_sr_logo": {"arabic_text"},
        "fresh_qa_a12_transparent_arabic": {"arabic_text"},
        "fresh_qa_a13_displaynone_arabic": {"arabic_text"},
        "fresh_qa_a15_dup_logo_realleft": {"elements_fit_1280", "elements_fit_360"},
        "fresh_qa_a17_dup_phone_second_bare": {"elements_fit_1280", "elements_fit_360"},
        "fresh_qa_a35_clip_path_form": {"elements_fit_1280", "elements_fit_360"},
        "fresh_qa_a37_next_behind_overlay": {
            "arabic_text",
            "elements_fit_1280",
            "elements_fit_360",
        },
        "fresh_qa_a38_far_below_page": {"elements_fit_1280", "elements_fit_360"},
        "fresh_qa_a39_transparent_everything": {
            "arabic_text",
            "elements_fit_1280",
            "elements_fit_360",
            "readable_contrast_1280",
            "readable_contrast_360",
        },
        "fresh_qa_b01_body_slash_onload": {"static_page"},
        "fresh_qa_b02_body_quote_onload": {"static_page"},
        "fresh_qa_b03_img_slash_onerror": {
            "computed_direction",
            "icon_next",
            "on_side_logo",
            "order_rtl_nav",
            "root_dir_lang",
        },
        "fresh_qa_b04_svg_slash_onload": {"static_page"},
        "fresh_qa_b05_autofocus_onfocus": {"static_page"},
        "fresh_qa_b07_body_onpageshow": {"static_page"},
        "fresh_qa_g01_overlay_pointer_none": {"no_overlays_1280", "no_overlays_360"},
        "fresh_qa_g02_same_color_text": {"readable_contrast_1280", "readable_contrast_360"},
        "fresh_qa_g06_blend": {"no_effects_1280", "no_effects_360"},
        "fresh_qa_g07_filter_opacity0": {"no_effects_1280", "no_effects_360"},
        "fresh_qa_g10_foreignobject_overlay": {"no_overlays_1280", "no_overlays_360"},
        "fresh_qa_g11_text_color_alpha_low": {
            "arabic_text",
            "elements_fit_1280",
            "elements_fit_360",
            "readable_contrast_1280",
            "readable_contrast_360",
        },
        "fresh_qa_g14_text_indent": {"arabic_text"},
        "fresh_qa_g15_color_via_background_clip": {
            "readable_contrast_1280",
            "readable_contrast_360",
        },
        "iframe_srcdoc_patches_parent": {"static_page"},
        "inline_script_sets_dir": {"static_page"},
        "self_removing_script": {"static_page"},
        "fresh_planted_files": UNTOUCHED_FAILS["rtl-contact-page-build"],
    },
    LC: {
        "dist_only_edit": lc(["ltr_layout_unchanged"]),
        "ltr_variant": lc(["no_physical_css"]),
        "delete_island": lc(
            [
                "islands_direction",
                "ltr_islands_kept",
                "testids_and_text_kept",
                "ltr_layout_unchanged",
                "ltr_styles_unchanged",
            ],
            ["billing"],
        ),
        "hide_island": lc(["testids_and_text_kept"], ["notifications"]),
        "shrink_main": lc(["ltr_islands_kept", "ltr_layout_unchanged"], ["index"]),
        "style_element": lc(["css_from_build"], ["index"]),
        # utilities dropped or put on the wrong side without moving a box
        "wrong_side_nav_border": lc(["ltr_styles_unchanged"], ["index"]),
        "drop_border_colour": lc(["ltr_styles_unchanged"], ["billing"]),
        "drop_plan_radius": lc(["ltr_styles_unchanged"], ["billing"]),
        # code that removes itself after setting dir/lang or restyling (QA, PR 57)
        "self_removing_script": lc(["css_from_build"], ["index"]),
        "dir_lang_by_script": lc(["css_from_build"], ["billing"]),
        # Arabic pages that do not mirror while LTR stays intact (QA, PR 57)
        "rtl_direction_ltr_hack": lc(["rtl_mirrors_ltr"], ["notifications", "billing"]),
        "rtl_variant_wrong_side": lc(["rtl_mirrors_ltr"], ["index"]),
        # a classless wrapper shifts every path: missing paths fail, nothing is skipped
        "wrapper_hides_styles": lc(["ltr_layout_unchanged", "ltr_styles_unchanged"], ["billing"]),
        # a wrapper forced left-to-right is not an island: it and its content must mirror
        "body_dir_ltr": lc(["rtl_mirrors_ltr"]),
        "body_dir_auto": lc(["rtl_mirrors_ltr", "ltr_layout_unchanged", "ltr_styles_unchanged"]),
        "main_dir_ltr": lc(["rtl_mirrors_ltr"], ["index"]),
        "main_css_direction_ltr": lc(["rtl_mirrors_ltr"]),
        # rtl_mirrors_ltr comes only from the computed-direction rule (box, styles and resolved
        # text-align all mirror); text-align: right is what no_physical_css sees
        "title_direction_only": lc(["rtl_mirrors_ltr", "no_physical_css"]),
        # an island testid on a wrapper does not make it an island
        "body_island_testid": lc(
            ["rtl_mirrors_ltr", "testids_and_text_kept", "ltr_layout_unchanged"]
        ),
        "main_island_testid": lc(
            ["rtl_mirrors_ltr", "testids_and_text_kept", "ltr_layout_unchanged"], ["index"]
        ),
        # fresh fixture, lang and dir set, body flipped with scaleX(-1)
        "fresh_mirror_body": lc(
            [
                "ltr_islands_kept",
                "rtl_mirrors_ltr",
                "no_physical_tailwind",
                "ltr_layout_unchanged",
                "no_physical_css",
            ]
        ),
    },
}

# Runs inside the container. Arguments: the mutation names; $ALTS and $GAMES list the alternative
# solutions (run on a fresh fixture) and the gaming cases (run on top of the reference). Each case
# works on a fresh copy of /app; a failing setup step or a crashing verify.py is recorded as a
# failure, never skipped.
CASES_SCRIPT = r"""
mkdir -p /logs/verifier /cases /work
[ -d /opt/kilmeh-build ] && cp -a /opt/kilmeh-build /pristine
run_case() {
  name=$1; shift
  # a case may tamper with the grading toolchain under /opt: restore it between cases
  [ -d /pristine ] && rm -rf /opt/kilmeh-build && cp -a /pristine /opt/kilmeh-build
  dir=/work/$name; out=/tmp/out-$name
  rm -rf "$dir" "$out"; mkdir -p "$dir"; cp -a /app/. "$dir"/
  for step in "$@"; do
    if ! ( cd "$dir" && bash -c "$step" ) >/dev/null 2>&1; then
      echo '{"__setup_failed__": false}' > /cases/$name.json
      echo 255 > /cases/$name.rc; return
    fi
  done
  if ! bash /tests/build.sh "$dir" "$out" >/dev/null 2>&1; then
    echo '{"__build_failed__": false}' > /cases/$name.json
    echo 255 > /cases/$name.rc; return
  fi
  python3 -I /tests/verify.py "$dir" "$out" > /cases/$name.json 2>/cases/$name.err
  echo $? > /cases/$name.rc
}
run_case untouched
run_case known-bad "bash /solution-bad/solve.sh"
run_case reference "bash /solution/solve.sh"
for m in "$@"; do
  run_case "mut-$m" "bash /solution/solve.sh" "python3 /mutations/$m.py"
done
for a in $ALTS; do
  run_case "alt-$a" "python3 /alternatives/$a.py"
done
for g in $GAMES; do
  case $g in
    fresh_*) run_case "game-$g" "python3 /gaming/$g.py" ;;
    *) run_case "game-$g" "bash /solution/solve.sh" "python3 /gaming/$g.py" ;;
  esac
done
python3 - <<'PY'
import glob, json, os
merged = {}
for path in sorted(glob.glob("/cases/*.json")):
    name = os.path.basename(path)[:-5]
    try:
        checks = json.load(open(path))
    except ValueError:
        checks = {"__verify_crashed__": False}
    rc = int(open(path[:-5] + ".rc").read().strip() or 255)
    merged[name] = {"checks": checks, "rc": rc}
json.dump(merged, open("/logs/verifier/cases.json", "w"))
PY
"""


def run_task(
    task_dir: Path,
    mutations: dict[str, Path],
    alternatives: dict[str, Path] | None = None,
    gaming: dict[str, Path] | None = None,
) -> dict[str, dict]:
    """Build the task image and run every case in one container.

    Returns case -> {"checks": {check: bool}, "rc": verify.py exit status}.
    """
    task_dir = task_dir.resolve()
    tag = f"kilmeh-rtltest-{task_dir.name}"
    build = subprocess.run(
        selftest.build_command(task_dir, tag),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=BUILD_TIMEOUT,
    )
    assert build.returncode == 0, "docker build failed: " + (build.stdout + build.stderr)[-800:]
    alternatives, gaming = alternatives or {}, gaming or {}
    for group in (mutations, alternatives, gaming):
        for key, script in group.items():
            assert re.fullmatch(r"[a-z0-9_.]+", key) and script.name == f"{key}.py", script
    name = f"{tag}-{time.time_ns()}"
    with tempfile.TemporaryDirectory() as scratch:
        mutdir = Path(scratch) / "mutations"
        mutdir.mkdir()
        extra = {}
        for label, group in (
            ("mutations", mutations),
            ("alternatives", alternatives),
            ("gaming", gaming),
        ):
            folder = mutdir if label == "mutations" else Path(scratch) / label
            folder.mkdir(exist_ok=True)
            extra[label] = folder
            for key, script in group.items():
                shutil.copy(script, folder / f"{key}.py")
        cmd = ["docker", "run", "--name", name, "--network", "none"]
        cmd += ["-v", f"{task_dir / 'tests'}:/tests:ro"]
        cmd += ["-v", f"{task_dir / 'solutions/reference'}:/solution:ro"]
        cmd += ["-v", f"{task_dir / 'solutions/known-bad'}:/solution-bad:ro"]
        cmd += ["-v", f"{mutdir}:/mutations:ro", "-v", f"{extra['alternatives']}:/alternatives:ro"]
        cmd += ["-v", f"{extra['gaming']}:/gaming:ro", "-e", f"ALTS={' '.join(alternatives)}"]
        cmd += ["-e", f"GAMES={' '.join(gaming)}", "-w", "/app", tag]
        cmd += ["bash", "-c", CASES_SCRIPT, "cases", *mutations]
        try:
            subprocess.run(cmd, capture_output=True, timeout=RUN_TIMEOUT)
            copied = subprocess.run(
                ["docker", "cp", f"{name}:/logs/verifier/cases.json", f"{scratch}/cases.json"],
                capture_output=True,
                text=True,
            )
            assert copied.returncode == 0, "no cases.json: " + copied.stderr[-400:]
            return json.loads((Path(scratch) / "cases.json").read_text("utf-8"))
        finally:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=60)


@functools.cache
def cases_for(task_id: str) -> dict[str, dict]:
    task_dir = ROOT / "tasks" / "c-rtl-ui" / task_id
    assert task_dir.is_dir(), f"missing task {task_dir}"
    scripts = {p.stem: p for p in sorted((MUTATIONS / task_id).glob("*.py"))}
    alts = {p.stem: p for p in sorted((ALTERNATIVES / task_id).glob("*.py"))}
    games = {p.stem: p for p in sorted((GAMING / task_id).glob("*.py"))}
    return run_task(task_dir, scripts, alts, games)


def failed(case: dict) -> set[str]:
    return {key for key, ok in case["checks"].items() if not ok}


@pytest.mark.parametrize("task", sorted(CHECKS))
def test_check_list_matches_the_plan(task):
    reference = cases_for(task)["reference"]["checks"]
    assert set(reference) == set(CHECKS[task])
    scripts = {p.stem for p in (MUTATIONS / task).glob("*.py")}
    assert scripts == set(CHECKS[task]), "one mutation script per check"


@pytest.mark.parametrize("task", sorted(CHECKS))
def test_reference_passes(task):
    case = cases_for(task)["reference"]
    assert case["checks"] and all(case["checks"].values()), failed(case)
    assert case["rc"] == 0, "verify.py must exit 0 when every check passes"


@pytest.mark.parametrize("task", sorted(CHECKS))
def test_known_bad_fails(task):
    case = cases_for(task)["known-bad"]
    assert failed(case) == KNOWN_BAD_FAILS[task]
    assert case["rc"] != 0, "verify.py must exit non-zero when a check fails"


@pytest.mark.parametrize("task", sorted(CHECKS))
def test_untouched_fails(task):
    case = cases_for(task)["untouched"]
    assert failed(case) == UNTOUCHED_FAILS[task]
    assert case["rc"] != 0, "verify.py must exit non-zero when a check fails"


@pytest.mark.parametrize(
    ("task", "check"), [(t, c) for t in sorted(CHECKS) for c in CHECKS[t]], ids=lambda v: v
)
def test_each_check_fails_in_isolation(task, check):
    case = cases_for(task)[f"mut-{check}"]
    assert failed(case) == {check}
    assert case["rc"] != 0


def _cases(root: Path) -> list[tuple[str, str]]:
    return [(t, p.stem) for t in sorted(CHECKS) for p in sorted((root / t).glob("*.py"))]


@pytest.mark.parametrize(("task", "name"), _cases(ALTERNATIVES), ids=lambda v: v)
def test_alternative_solution_passes(task, name):
    """A different, correct technique than the reference must score 1 (fairness)."""
    case = cases_for(task)[f"alt-{name}"]
    assert case["checks"] and all(case["checks"].values()), failed(case)
    assert case["rc"] == 0


@pytest.mark.parametrize(("task", "name"), _cases(GAMING), ids=lambda v: v)
def test_gaming_case_fails_the_expected_checks(task, name):
    """Hiding, clipping, shrinking or editing dist/ never scores 1; the failing set is pinned."""
    case = cases_for(task)[f"game-{name}"]
    assert failed(case) == GAMING_FAILS[task][name]
    assert case["rc"] != 0
