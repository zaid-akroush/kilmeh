"""Mutation for rtl-contact-page-build: an inline script is added to the page.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
assert "</body>" in text
path.write_text(text.replace("</body>", "<script>void 0</script></body>", 1), encoding="utf-8")
