# Reference solution: optional currency argument.
import sys

p = sys.argv[1] if len(sys.argv) > 1 else "/app/price.py"
new = """def format_price(amount, currency="JOD"):
    return f"{amount:.2f} {currency}"


def line_text(name, amount):
    return f"{name}: {format_price(amount)}"
"""
with open(p, "wb") as f:
    f.write(new.encode("utf-8"))
