"""Alternative for rtl-bidi-data-cells: CSS `direction: ltr; unicode-bidi: isolate` on the
values, no markup change.

Runs in the app directory on the untouched fixture.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as css:
    css.write("\n.value code,\n.value .phone {\n  direction: ltr;\n  unicode-bidi: isolate;\n}\n")
