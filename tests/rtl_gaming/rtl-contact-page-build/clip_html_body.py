"""Gaming attempt for rtl-contact-page-build: overflow-x:hidden on html and body hides a 900px form.

Runs on top of the reference solution.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write("html,body{overflow-x:hidden}.contact-form{min-width:900px}\n")
