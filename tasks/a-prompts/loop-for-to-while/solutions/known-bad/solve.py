# Known-bad solution: keeps the for loop (results still correct), so the AST check must fail.
import sys

p = sys.argv[1] if len(sys.argv) > 1 else "/app/numbers.py"
new = """def sum_positive(numbers):
    total = 0
    for n in numbers:
        if n > 0:
            total += n
    return total
"""
with open(p, "wb") as f:
    f.write(new.encode("utf-8"))
