def _calculate_shipping(order_subtotal):
    """Return shipping cost based on order subtotal."""
    if order_subtotal < 50:
        return 5.99
    elif order_subtotal < 100:
        return 3.99
    else:
        return 0


def calculate_invoice(orders):
    """Calculate total invoice amount from orders."""
    subtotal = 0
    tax_total = 0
    shipping_total = 0
    for order in orders:
        if order.get("status") == "cancelled":
            continue
        items = order.get("items", [])
        order_subtotal = 0
        for item in items:
            price = item.get("price", 0)
            quantity = item.get("quantity", 1)
            discount = item.get("discount", 0)
            order_subtotal += price * quantity * (1 - discount)
        subtotal += order_subtotal
        tax_rate = order.get("tax_rate", 0.08)
        order_tax = order_subtotal * tax_rate
        tax_total += order_tax
        shipping_total += _calculate_shipping(order_subtotal)
    total = subtotal + tax_total + shipping_total
    return {
        "subtotal": round(subtotal, 2),
        "tax": round(tax_total, 2),
        "shipping": round(shipping_total, 2),
        "total": round(total, 2)
    }
