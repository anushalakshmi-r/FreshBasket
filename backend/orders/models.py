import secrets

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


def generate_order_number():
    return f"FB-{secrets.token_hex(8).upper()}"


class Order(models.Model):
    class PaymentMethod(models.TextChoices):
        COD = "cod", "Cash on Delivery"
        ONLINE = "online", "Online"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    class OrderStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        PACKED = "packed", "Packed"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    order_number = models.CharField(
        max_length=20,
        unique=True,
        default=generate_order_number,
        editable=False,
    )
    delivery_address_snapshot = models.JSONField()
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    grand_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices)
    payment_status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    order_status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    customer_notes = models.TextField(blank=True)
    coupon_code = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["customer", "-created_at"], name="orders_customer_created"),
            models.Index(fields=["order_status", "created_at"], name="orders_status_created"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(subtotal__gte=0),
                name="orders_subtotal_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(delivery_fee__gte=0),
                name="orders_delivery_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(discount__gte=0),
                name="orders_discount_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(grand_total__gte=0),
                name="orders_total_nonnegative",
            ),
        ]

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.SET_NULL,
        related_name="order_items",
        null=True,
        blank=True,
    )
    product_name_snapshot = models.CharField(max_length=200)
    sku_snapshot = models.CharField(max_length=40)
    product_image_snapshot = models.URLField(max_length=500, blank=True)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        ordering = ["id"]
        indexes = [models.Index(fields=["order", "product"], name="orders_item_lookup")]
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gte=1), name="orders_item_qty_positive"),
            models.CheckConstraint(condition=Q(unit_price__gte=0), name="orders_unit_price_nonnegative"),
            models.CheckConstraint(condition=Q(line_total__gte=0), name="orders_line_total_nonnegative"),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product_name_snapshot}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=20, choices=Order.OrderStatus.choices)
    note = models.CharField(max_length=255, blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class Coupon(models.Model):
    code = models.CharField(max_length=40, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_fixed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    minimum_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    per_customer_limit = models.PositiveIntegerField(default=1)
    is_enabled = models.BooleanField(default=True)

    def calculate_discount(self, subtotal):
        from decimal import Decimal
        amount = subtotal * self.discount_percentage / Decimal("100") if self.discount_percentage is not None else (self.discount_fixed or Decimal("0"))
        if self.maximum_discount is not None:
            amount = min(amount, self.maximum_discount)
        return min(amount, subtotal).quantize(Decimal("0.01"))


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.PROTECT, related_name="usages")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="coupon_usages")
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="coupon_usage")
    created_at = models.DateTimeField(auto_now_add=True)
