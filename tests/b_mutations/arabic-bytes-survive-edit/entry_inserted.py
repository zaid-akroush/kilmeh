"""Mutation: The checkout_subtitle line is not inserted.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

ts = Path("src/strings.ts")
csv = Path("locale/ar.csv")
readme = Path("README.md")

lines = ts.read_bytes().split(b"\n")
ts.write_bytes(b"\n".join(ln for ln in lines if not ln.startswith(b"  checkout_subtitle:")))
