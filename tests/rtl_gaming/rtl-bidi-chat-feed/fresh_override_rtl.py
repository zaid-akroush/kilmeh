"""Gaming attempt for rtl-bidi-chat-feed (review probe): the override stays and the Arabic-first
messages are switched to direction rtl. The run order of the Latin tokens looks right, but their
letters are reversed, and the Arabic in m2 and m3 still reads backwards.

Runs in the app directory on the untouched fixture.
"""

from pathlib import Path

with Path("styles.css").open("a", encoding="utf-8") as f:
    f.write(
        '[data-testid="m1"] .text,[data-testid="m4"] .text,[data-testid="m5"] .text'
        "{direction:rtl}\n"
    )
