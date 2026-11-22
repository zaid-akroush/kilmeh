# Reference solution: rewrite the for loop as a while loop.
import sys

p = sys.argv[1] if len(sys.argv) > 1 else "/app/numbers.py"
new = """def sum_positive(numbers):
    total = 0
    i = 0
    while i < len(numbers):
        n = numbers[i]
        if n > 0:
            total += n
        i += 1
    return total
"""
with open(p, "wb") as f:
    f.write(new.encode("utf-8"))
