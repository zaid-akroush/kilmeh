"""Mutation: U+FDF2 is expanded to its letters.

Runs in the app directory on top of the reference solution.
"""

from pathlib import Path

ts = Path("src/strings.ts")
csv = Path("locale/ar.csv")
readme = Path("README.md")

ts.write_bytes(
    ts.read_bytes().replace(
        chr(0xFDF2).encode("utf-8"), "".join(map(chr, (0x627, 0x644, 0x644, 0x647))).encode("utf-8")
    )
)
