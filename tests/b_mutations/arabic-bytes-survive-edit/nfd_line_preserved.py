"""Mutation: Alef + U+0653 is composed to U+0622.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

ts = Path("src/strings.ts")
csv = Path("locale/ar.csv")
readme = Path("README.md")

old = (chr(0x627) + chr(0x653)).encode("utf-8")
ts.write_bytes(ts.read_bytes().replace(old, chr(0x622).encode("utf-8")))
