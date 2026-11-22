from decimal import Decimal

DELIVERY_FREE_THRESHOLD = Decimal("499.00")
STANDARD_DELIVERY_FEE = Decimal("40.00")


def calculate_delivery_fee(subtotal):
    if subtotal <= 0 or subtotal >= DELIVERY_FREE_THRESHOLD:
        return Decimal("0.00")
    return STANDARD_DELIVERY_FEE
