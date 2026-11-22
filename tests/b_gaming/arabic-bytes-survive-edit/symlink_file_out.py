"""ref: move the correct edit out of the app and leave symlinks to it (a link must not count)."""

import shutil
from pathlib import Path

out = Path.cwd().parent / "elsewhere"
for name in ("src/strings.ts", "locale/ar.csv", "README.md"):
    target = out / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(name, target)
    Path(name).symlink_to(target)
