"""Mutation for rtl-tailwind-sidebar: a physical padding-left:1px on the footer note, in input.css.

It changes no geometry the other checks read.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("src/input.css").open("a", encoding="utf-8") as f:
    f.write("[data-testid=footer-note] { padding-left: 1px; }\n")
