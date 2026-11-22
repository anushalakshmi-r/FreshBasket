from django.db import models
from django.db.models import Q


class Payment(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        AUTHORIZED = "authorized", "Authorized"
        CAPTURED = "captured", "Captured"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        REFUND_REQUIRED = "refund_required", "Refund required"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="payment_attempts",
    )
    razorpay_order_id = models.CharField(max_length=50, db_index=True)
    razorpay_payment_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    payment_status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
    )
    payment_method = models.CharField(max_length=30, blank=True)
    signature_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [
            models.Index(
                fields=["order", "payment_status"],
                name="payments_order_status",
            ),
            models.Index(
                fields=["payment_status", "created_at"],
                name="payments_status_created",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gte=0),
                name="payments_amount_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.razorpay_order_id} ({self.payment_status})"


class WebhookEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=80)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="webhook_events",
    )
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-received_at", "-pk"]
        indexes = [models.Index(fields=["event_type", "received_at"], name="payments_event_type_time")]

    def __str__(self):
        return f"{self.event_type} ({self.event_id})"
