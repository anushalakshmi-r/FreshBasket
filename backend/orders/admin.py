from django.contrib import admin

from orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = (
        "product",
        "product_name_snapshot",
        "sku_snapshot",
        "product_image_snapshot",
        "unit_price",
        "quantity",
        "line_total",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer",
        "grand_total",
        "payment_method",
        "payment_status",
        "order_status",
        "created_at",
    )
    search_fields = ("order_number", "customer__email", "customer__username")
    list_filter = ("order_status", "payment_method", "payment_status", "created_at")
    ordering = ("-created_at",)
    readonly_fields = (
        "customer",
        "order_number",
        "delivery_address_snapshot",
        "subtotal",
        "delivery_fee",
        "discount",
        "grand_total",
        "payment_method",
        "payment_status",
        "order_status",
        "customer_notes",
        "created_at",
        "updated_at",
    )
    inlines = (OrderItemInline,)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "product_name_snapshot",
        "sku_snapshot",
        "order",
        "quantity",
        "unit_price",
        "line_total",
    )
    search_fields = ("product_name_snapshot", "sku_snapshot", "order__order_number")
    list_filter = ("order__order_status", "order__created_at")
    ordering = ("-order__created_at", "id")
    readonly_fields = (
        "order",
        "product",
        "product_name_snapshot",
        "sku_snapshot",
        "product_image_snapshot",
        "unit_price",
        "quantity",
        "line_total",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
