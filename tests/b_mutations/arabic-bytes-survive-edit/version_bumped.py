"""Mutation: The VERSION line is left at 2.3.0.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

ts = Path("src/strings.ts")
csv = Path("locale/ar.csv")
readme = Path("README.md")

ts.write_bytes(ts.read_bytes().replace(b"2.4.0", b"2.3.0"))
