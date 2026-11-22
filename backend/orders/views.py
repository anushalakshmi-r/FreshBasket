from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from orders.serializers import (
    CheckoutRequestSerializer,
    OrderSerializer,
    OrderStatusUpdateSerializer,
)
from orders.services import (
    ADMIN_STATUS_TRANSITIONS,
    cancel_order,
    checkout_quote,
    create_order,
)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(checkout_quote(request.user))

    def post(self, request):
        serializer = CheckoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = create_order(
            customer=request.user,
            address_id=serializer.validated_data["address_id"],
            payment_method=serializer.validated_data["payment_method"],
            customer_notes=serializer.validated_data.get("customer_notes", ""),
        )
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = (
            Order.objects.filter(customer=request.user)
            .prefetch_related("items")
            .order_by("-created_at", "-pk")
        )
        return Response(OrderSerializer(orders, many=True).data)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        order = get_object_or_404(
            Order.objects.prefetch_related("items"),
            customer=request.user,
            order_number=order_number,
        )
        return Response(OrderSerializer(order).data)


class OrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_number):
        order = cancel_order(customer=request.user, order_number=order_number)
        return Response(OrderSerializer(order).data)


class OrderStatusUpdateView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, order_number):
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        next_status = serializer.validated_data["order_status"]

        with transaction.atomic():
            order = get_object_or_404(
                Order.objects.select_for_update(),
                order_number=order_number,
            )
            allowed = ADMIN_STATUS_TRANSITIONS.get(order.order_status, set())
            if next_status not in allowed:
                return Response(
                    {
                        "detail": (
                            f"Cannot move an order from {order.order_status} "
                            f"to {next_status}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            order.order_status = next_status
            order.save(update_fields=["order_status", "updated_at"])

        return Response(OrderSerializer(order).data)
