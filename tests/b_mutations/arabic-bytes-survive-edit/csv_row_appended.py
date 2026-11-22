"""Mutation: The CSV row is not appended.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

ts = Path("src/strings.ts")
csv = Path("locale/ar.csv")
readme = Path("README.md")

lines = csv.read_bytes().split(b"\r\n")
csv.write_bytes(b"\r\n".join(ln for ln in lines if not ln.startswith(b"checkout_subtitle,")))
