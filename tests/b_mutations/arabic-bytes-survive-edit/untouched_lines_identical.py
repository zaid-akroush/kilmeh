"""Mutation: Only the trailing spaces of the `trailing` line are trimmed.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

ts = Path("src/strings.ts")
csv = Path("locale/ar.csv")
readme = Path("README.md")

ts.write_bytes(ts.read_bytes().replace(b",   \n", b",\n"))
