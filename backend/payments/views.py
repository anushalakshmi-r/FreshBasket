from decimal import Decimal

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from payments.models import Payment
from payments.serializers import CreatePaymentOrderSerializer, VerifyPaymentSerializer
from payments.services import (
    parse_webhook_body,
    process_webhook,
    verify_checkout_payment,
    verify_webhook_signature,
    webhook_event_id,
    create_razorpay_order,
)


class PaymentCreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreatePaymentOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment, created = create_razorpay_order(
            customer=request.user,
            order_number=serializer.validated_data["order_number"],
        )
        amount_paise = int((payment.amount * Decimal("100")).quantize(Decimal("1")))
        return Response(
            {
                "key_id": settings.RAZORPAY_KEY_ID,
                "razorpay_order_id": payment.razorpay_order_id,
                "order_number": payment.order.order_number,
                "amount": amount_paise,
                "currency": payment.currency,
                "payment_status": payment.payment_status,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class PaymentVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order, payment, state = verify_checkout_payment(
            customer=request.user,
            **serializer.validated_data,
        )
        return Response(
            {
                "order_number": order.order_number,
                "order_payment_status": order.payment_status,
                "order_status": order.order_status,
                "payment_attempt_status": payment.payment_status,
                "state": state,
            }
        )


class PaymentWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        signature = request.headers.get("X-Razorpay-Signature", "")
        if not signature or not verify_webhook_signature(request.body, signature):
            return Response(
                {"detail": "Razorpay webhook signature is invalid."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payload = parse_webhook_body(request.body)
        event_id = webhook_event_id(
            request.body,
            request.headers.get("X-Razorpay-Event-Id", ""),
        )
        result = process_webhook(event_id=event_id, payload=payload)
        return Response({"status": result})


class PaymentOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        order = get_object_or_404(
            Order.objects.filter(customer=request.user),
            order_number=order_number,
        )
        attempt = order.payment_attempts.first()
        configured = bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)
        retryable = (
            configured
            and order.payment_method == Order.PaymentMethod.ONLINE
            and order.order_status != Order.OrderStatus.CANCELLED
            and order.payment_status
            in (Order.PaymentStatus.PENDING, Order.PaymentStatus.FAILED)
            and (
                attempt is None
                or attempt.payment_status != Payment.Status.AUTHORIZED
            )
        )
        return Response(
            {
                "order_number": order.order_number,
                "payment_method": order.payment_method,
                "payment_status": order.payment_status,
                "order_status": order.order_status,
                "amount": order.grand_total,
                "currency": "INR",
                "configured": configured,
                "can_retry": retryable,
                "latest_attempt_status": attempt.payment_status if attempt else None,
            }
        )
