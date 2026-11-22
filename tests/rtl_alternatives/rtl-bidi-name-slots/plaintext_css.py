"""Alternative for rtl-bidi-name-slots: `unicode-bidi: plaintext` on .slot (isolated, direction
from the value's first strong letter).

Runs in the app directory on the untouched fixture.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as css:
    css.write("\n.slot {\n  unicode-bidi: plaintext;\n}\n")
