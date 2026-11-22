"""Known-bad solution: the whole value column is switched to left to right.

The Arabic words move to the left of the values and the phone number groups still come out
reversed. Runs in the app directory.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as css:
    css.write("\n.info td.value {\n  direction: ltr;\n}\n")
