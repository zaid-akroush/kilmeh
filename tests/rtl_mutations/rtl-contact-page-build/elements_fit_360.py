"""Mutation for rtl-contact-page-build: form wider than the screen, hidden by overflow on main.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write("@media (max-width:500px){main{overflow-x:hidden}.contact-form{min-width:600px}}\n")
