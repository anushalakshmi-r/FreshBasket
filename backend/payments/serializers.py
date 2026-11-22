from rest_framework import serializers


class CreatePaymentOrderSerializer(serializers.Serializer):
    order_number = serializers.CharField(max_length=20)


class VerifyPaymentSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField(max_length=50)
    razorpay_payment_id = serializers.CharField(max_length=50)
    razorpay_signature = serializers.CharField(
        max_length=128,
        required=False,
        allow_blank=False,
    )
