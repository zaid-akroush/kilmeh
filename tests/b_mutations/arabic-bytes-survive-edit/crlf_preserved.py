"""Mutation: locale/ar.csv is converted to LF line endings.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

ts = Path("src/strings.ts")
csv = Path("locale/ar.csv")
readme = Path("README.md")

csv.write_bytes(csv.read_bytes().replace(b"\r\n", b"\n"))
