"""Mutation: A UTF-8 BOM is put at the start of strings.ts.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

ts = Path("src/strings.ts")
csv = Path("locale/ar.csv")
readme = Path("README.md")

ts.write_bytes(b"\xef\xbb\xbf" + ts.read_bytes())
