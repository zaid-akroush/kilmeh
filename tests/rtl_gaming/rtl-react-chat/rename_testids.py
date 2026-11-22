"""Gaming attempt for rtl-react-chat: the own-bubble testid is renamed.

Runs in the app directory on top of the reference.
"""

from pathlib import Path

path = Path("src/Chat.jsx")
text = path.read_text(encoding="utf-8")
old, new = 'data-testid="bubble-me"', 'data-testid="bubble-mine"'
assert old in text, "reference changed: update this mutation"
path.write_text(text.replace(old, new), encoding="utf-8")
