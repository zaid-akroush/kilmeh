def invoice_total(prices):
    subtotal = 0
    for p in prices:
        subtotal += p
    return round(subtotal * 1.16, 2)


def receipt_line(name, price):
    total = round(price * 1.16, 2)
    return f"{name}: {total:.2f}"
