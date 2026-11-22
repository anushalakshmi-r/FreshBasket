from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from accounts.models import CustomerAddress
from cart.models import Cart, CartItem
from catalog.models import Inventory, Product
from orders.models import Order, OrderItem
from orders.pricing import calculate_delivery_fee


def _address_snapshot(address):
    return {
        "full_name": address.full_name,
        "phone_number": address.phone_number,
        "address_line_1": address.address_line_1,
        "address_line_2": address.address_line_2,
        "landmark": address.landmark,
        "city": address.city,
        "state": address.state,
        "postal_code": address.postal_code,
        "address_type": address.address_type,
    }


def _primary_image(product):
    images = list(product.images.all())
    image = next((candidate for candidate in images if candidate.is_primary), None)
    image = image or (images[0] if images else None)
    return image.image_url if image else ""


def checkout_quote(customer):
    cart, _ = Cart.objects.get_or_create(customer=customer)
    items = list(
        CartItem.objects.filter(cart=cart)
        .select_related("product")
        .prefetch_related("product__images", "product__inventory")
        .order_by("product_id")
    )
    subtotal = sum(
        (item.product.selling_price * item.quantity for item in items),
        Decimal("0.00"),
    )
    delivery_fee = calculate_delivery_fee(subtotal)
    return {
        "items": [
            {
                "product_id": item.product_id,
                "product_name": item.product.name,
                "image_url": _primary_image(item.product),
                "quantity": item.quantity,
                "unit_price": item.product.selling_price,
                "line_total": item.product.selling_price * item.quantity,
                "available_stock": item.product.available_quantity,
            }
            for item in items
        ],
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "discount": Decimal("0.00"),
        "grand_total": subtotal + delivery_fee,
        "free_delivery_threshold": Decimal("499.00"),
    }


@transaction.atomic
def create_order(*, customer, address_id, payment_method, customer_notes=""):
    cart, _ = Cart.objects.get_or_create(customer=customer)
    cart = Cart.objects.select_for_update().get(pk=cart.pk)
    cart_items = list(
        CartItem.objects.select_for_update()
        .filter(cart=cart)
        .order_by("product_id")
    )
    if not cart_items:
        raise ValidationError({"detail": "Your basket is empty."})

    address = (
        CustomerAddress.objects.select_for_update()
        .filter(pk=address_id, customer=customer)
        .first()
    )
    if address is None:
        raise ValidationError({"address_id": "Select one of your saved delivery addresses."})

    product_ids = [item.product_id for item in cart_items]
    products = {
        product.pk: product
        for product in Product.objects.select_for_update()
        .filter(pk__in=product_ids)
        .prefetch_related("images")
        .order_by("pk")
    }
    inventories = {
        inventory.product_id: inventory
        for inventory in Inventory.objects.select_for_update()
        .filter(product_id__in=product_ids)
        .order_by("product_id")
    }
    validated_lines = []
    subtotal = Decimal("0.00")
    for cart_item in cart_items:
        product = products.get(cart_item.product_id)
        if product is None or not product.is_active:
            raise ValidationError(
                {"detail": "A product in your basket is no longer available. Review your basket."}
            )
        inventory = inventories.get(product.pk)
        available = inventory.available_quantity if inventory else 0
        if cart_item.quantity > available:
            raise ValidationError(
                {
                    "detail": (
                        f"Only {available} unit(s) of {product.name} are currently available. "
                        "Update your basket and try again."
                    ),
                    "product_id": product.pk,
                    "available_stock": available,
                }
            )
        line_total = product.selling_price * cart_item.quantity
        subtotal += line_total
        validated_lines.append((cart_item, product, inventory, line_total))

    delivery_fee = calculate_delivery_fee(subtotal)
    discount = Decimal("0.00")
    order = Order.objects.create(
        customer=customer,
        delivery_address_snapshot=_address_snapshot(address),
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        discount=discount,
        grand_total=subtotal + delivery_fee - discount,
        payment_method=payment_method,
        payment_status=Order.PaymentStatus.PENDING,
        order_status=Order.OrderStatus.PENDING,
        customer_notes=customer_notes,
    )

    for cart_item, product, inventory, line_total in validated_lines:
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name_snapshot=product.name,
            sku_snapshot=product.sku,
            product_image_snapshot=_primary_image(product),
            unit_price=product.selling_price,
            quantity=cart_item.quantity,
            line_total=line_total,
        )
        inventory.stock_quantity -= cart_item.quantity
        inventory.save(update_fields=["stock_quantity", "updated_at"])

    cart.items.all().delete()
    return Order.objects.prefetch_related("items").get(pk=order.pk)


@transaction.atomic
def cancel_order(*, customer, order_number):
    order = (
        Order.objects.select_for_update()
        .filter(customer=customer, order_number=order_number)
        .first()
    )
    if order is None:
        raise NotFound("Order not found.")
    if order.payment_status == Order.PaymentStatus.PAID:
        raise ValidationError({"detail": "A paid order can no longer be cancelled."})
    if order.order_status not in (
        Order.OrderStatus.PENDING,
        Order.OrderStatus.CONFIRMED,
    ):
        raise ValidationError(
            {"detail": "This order can no longer be cancelled."}
        )

    from payments.models import Payment

    active_payments = Payment.objects.select_for_update().filter(
        order=order,
        payment_status__in=(Payment.Status.CREATED, Payment.Status.AUTHORIZED),
    )
    active_payments.update(
        payment_status=Payment.Status.CANCELLED,
        updated_at=timezone.now(),
    )

    order_items = list(order.items.select_related("product").order_by("product_id"))
    product_ids = [item.product_id for item in order_items if item.product_id]
    inventories = {
        inventory.product_id: inventory
        for inventory in Inventory.objects.select_for_update()
        .filter(product_id__in=product_ids)
        .order_by("product_id")
    }
    for item in order_items:
        if item.product_id is None:
            continue
        inventory = inventories.get(item.product_id)
        if inventory is None:
            raise ValidationError(
                {"detail": "Inventory is unavailable; contact support before cancelling."}
            )
        inventory.stock_quantity += item.quantity
        inventory.save(update_fields=["stock_quantity", "updated_at"])

    order.order_status = Order.OrderStatus.CANCELLED
    order.save(update_fields=["order_status", "updated_at"])
    return order


ADMIN_STATUS_TRANSITIONS = {
    Order.OrderStatus.PENDING: {Order.OrderStatus.CONFIRMED},
    Order.OrderStatus.CONFIRMED: {Order.OrderStatus.PROCESSING},
    Order.OrderStatus.PROCESSING: {Order.OrderStatus.SHIPPED},
    Order.OrderStatus.SHIPPED: {Order.OrderStatus.DELIVERED},
}
