"""Mutation for rtl-react-chat: own bubbles are not mirrored when dir flips to ltr.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

with Path("src/styles.css").open("a", encoding="utf-8") as f:
    f.write('[dir="ltr"] [data-testid="bubble-me"]{margin-inline:0 auto!important}' + "\n")
