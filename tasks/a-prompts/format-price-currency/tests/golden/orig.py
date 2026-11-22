def format_price(amount):
    return f"{amount:.2f} JOD"


def line_text(name, amount):
    return f"{name}: {format_price(amount)}"
