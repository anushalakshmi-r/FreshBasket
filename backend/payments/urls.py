from django.urls import path

from payments.views import (
    PaymentCreateOrderView,
    PaymentOrderStatusView,
    PaymentVerifyView,
    PaymentWebhookView,
)

urlpatterns = [
    path("create-order/", PaymentCreateOrderView.as_view(), name="payment-create-order"),
    path("verify/", PaymentVerifyView.as_view(), name="payment-verify"),
    path("webhook/", PaymentWebhookView.as_view(), name="payment-webhook"),
    path(
        "order/<str:order_number>/",
        PaymentOrderStatusView.as_view(),
        name="payment-order-status",
    ),
]
