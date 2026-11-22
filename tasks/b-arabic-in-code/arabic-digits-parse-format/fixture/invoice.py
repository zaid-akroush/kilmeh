"""Invoice totals. Uses numerals.py; amounts may be typed in any one digit system each."""

from decimal import Decimal

from numerals import format_number, parse_number


def total_text(amounts: list[str], system: str) -> str:
    """Sum the amounts and format the total with 2 decimal places in `system`."""
    total = sum((parse_number(a) for a in amounts), Decimal(0))
    return format_number(total, system, 2)
