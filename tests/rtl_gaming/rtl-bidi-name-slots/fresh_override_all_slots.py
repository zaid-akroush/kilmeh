"""Gaming attempt for rtl-bidi-name-slots (QA repro): every slot is isolated and forced left
to right with isolate-override, which reverses the Arabic name's letters.

Runs in the app directory on the untouched fixture.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write(".slot{unicode-bidi:isolate-override;direction:ltr}\n")
