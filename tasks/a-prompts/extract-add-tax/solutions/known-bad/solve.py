# Known-bad solution: add_tax exists and invoice_total uses it, but receipt_line repeats the math.
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
    total = round(price * 1.16, 2)
    return f"{name}: {total:.2f}"
"""
with open(p, "wb") as f:
    f.write(new.encode("utf-8"))
