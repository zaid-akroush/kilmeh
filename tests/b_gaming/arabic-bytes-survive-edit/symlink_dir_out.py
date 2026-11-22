"""ref: move the src and locale directories out and leave symlinks to them."""

import shutil
from pathlib import Path

out = Path.cwd().parent / "elsewhere"
out.mkdir()
for name in ("src", "locale"):
    shutil.move(name, out / name)
    Path(name).symlink_to(out / name)
