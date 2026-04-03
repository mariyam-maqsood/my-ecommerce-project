from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply two numbers"""
    try:
        return float(value) * int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_product(products, product_id):
    return products.get(id=int(product_id))

@register.filter
def multiply(value, arg):
    try:
        return float(value) * int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def total_cart_price(cart_items):
    return sum(item.product.price * item.quantity for item in cart_items)
