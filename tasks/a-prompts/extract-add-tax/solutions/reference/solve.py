# Reference solution: one add_tax helper used by both functions.
import sys

p = sys.argv[1] if len(sys.argv) > 1 else "/app/invoice.py"
new = """def add_tax(amount):
    return round(amount * 1.16, 2)


def invoice_total(prices):
    subtotal = 0
    for p in prices:
        subtotal += p
    return add_tax(subtotal)


def receipt_line(name, price):
    total = add_tax(price)
    return f"{name}: {total:.2f}"
"""
with open(p, "wb") as f:
    f.write(new.encode("utf-8"))
