"""Mutation: One invalid byte (0xFF) ends the first comment line of strings.ts.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

ts = Path("src/strings.ts")
csv = Path("locale/ar.csv")
readme = Path("README.md")

data = ts.read_bytes()
ts.write_bytes(data.replace(b"only edited.", b"only edited.\xff", 1))
