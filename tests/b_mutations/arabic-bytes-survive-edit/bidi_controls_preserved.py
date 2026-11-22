"""Mutation: RLM is dropped from the phone line.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

ts = Path("src/strings.ts")
csv = Path("locale/ar.csv")
readme = Path("README.md")

ts.write_bytes(ts.read_bytes().replace(chr(0x200F).encode("utf-8"), b"", 1))
