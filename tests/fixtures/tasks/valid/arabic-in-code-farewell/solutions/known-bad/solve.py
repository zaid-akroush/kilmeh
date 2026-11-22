# Known-bad solution: function works, but it strips bidi control characters and NFKC-normalizes
# (what a naive text-mode read/clean/write round trip does). Must FAIL the integrity checks.
import sys
import unicodedata
p = sys.argv[1] if len(sys.argv) > 1 else "/app/تحية.py"
s = open(p, encoding="utf-8").read()
for c in "‎‏⁦⁧⁨⁩":
    s = s.replace(c, "")
s = unicodedata.normalize("NFKC", s)
s += '''

def farewell(name):
    return f"وداعاً يا {name}!"
'''
open(p, "w", encoding="utf-8").write(s)
