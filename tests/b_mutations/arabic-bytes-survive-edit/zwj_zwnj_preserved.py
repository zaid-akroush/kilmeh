"""Mutation: ZWNJ is dropped from the zwnj line.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

ts = Path("src/strings.ts")
csv = Path("locale/ar.csv")
readme = Path("README.md")

ts.write_bytes(ts.read_bytes().replace(chr(0x200C).encode("utf-8"), b"", 1))
