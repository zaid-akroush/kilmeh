"""Mutation: A line is appended to README.md.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

ts = Path("src/strings.ts")
csv = Path("locale/ar.csv")
readme = Path("README.md")

readme.write_bytes(readme.read_bytes() + b"Edited.\n")
