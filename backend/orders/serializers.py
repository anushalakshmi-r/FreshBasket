from rest_framework import serializers

from orders.models import Order, OrderItem, OrderStatusHistory


class CheckoutRequestSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(min_value=1)
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)
    customer_notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    coupon_code = serializers.CharField(required=False, allow_blank=True, max_length=40)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name_snapshot",
            "sku_snapshot",
            "product_image_snapshot",
            "unit_price",
            "quantity",
            "line_total",
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "delivery_address_snapshot",
            "items",
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
            "coupon_code",
            "status_history",
        ]
        read_only_fields = fields

    def get_status_history(self, obj):
        return [{"status": item.status, "note": item.note, "created_at": item.created_at} for item in obj.status_history.all()]


class OrderStatusUpdateSerializer(serializers.Serializer):
    order_status = serializers.ChoiceField(choices=Order.OrderStatus.choices)
