"""Mutation: Shadda and fatha are put in canonical order (fatha first).

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

ts = Path("src/strings.ts")
csv = Path("locale/ar.csv")
readme = Path("README.md")

old = (chr(0x651) + chr(0x64E)).encode("utf-8")
new = (chr(0x64E) + chr(0x651)).encode("utf-8")
ts.write_bytes(ts.read_bytes().replace(old, new))
