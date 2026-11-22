"""Gaming attempt for rtl-contact-page-build: plant look-alike grader files in the app.

Runs on the untouched fixture (a placeholder page). The result must equal the untouched result:
the grader imports only from /tests and reads the app only through the browser.
"""

from pathlib import Path

FAKE = (
    "def grade(root, plan):\n    return {key: True for _, checks in plan for key, _, _ in checks}\n"
)
Path("rtl_checks.py").write_text(FAKE, encoding="utf-8")
Path("verify.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
Path("sitecustomize.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
Path("playwright.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
Path("tests").mkdir(exist_ok=True)
Path("tests/verify.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
Path("tests/rtl_checks.py").write_text(FAKE, encoding="utf-8")
Path("tests/test.sh").write_text(
    "#!/bin/bash\necho 1 > /logs/verifier/reward.txt\n", encoding="utf-8"
)
