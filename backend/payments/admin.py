from django.contrib import admin

from payments.models import Payment, WebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "razorpay_order_id",
        "razorpay_payment_id",
        "order",
        "amount",
        "currency",
        "payment_status",
        "signature_verified",
        "created_at",
    )
    search_fields = (
        "razorpay_order_id",
        "razorpay_payment_id",
        "order__order_number",
    )
    list_filter = ("payment_status", "currency", "signature_verified", "created_at")
    ordering = ("-created_at",)
    readonly_fields = (
        "order",
        "razorpay_order_id",
        "razorpay_payment_id",
        "amount",
        "currency",
        "payment_status",
        "payment_method",
        "signature_verified",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "event_type", "payment", "received_at", "processed_at")
    search_fields = ("event_id", "event_type", "payment__razorpay_payment_id")
    list_filter = ("event_type", "received_at", "processed_at")
    ordering = ("-received_at",)
    readonly_fields = ("event_id", "event_type", "payment", "received_at", "processed_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
