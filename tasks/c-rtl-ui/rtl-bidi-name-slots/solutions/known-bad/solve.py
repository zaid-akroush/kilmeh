"""Known-bad solution: isolates every slot but leaves it in the page's right-to-left direction.

The count after the name is fixed, but `Notes++` and `#A-1024` still lose their punctuation to
the wrong side. Runs in the app directory.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as css:
    css.write("\n.slot {\n  unicode-bidi: isolate;\n}\n")
