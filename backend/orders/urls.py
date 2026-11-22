from django.urls import path

from orders.views import (
    CheckoutView,
    OrderCancelView,
    OrderDetailView,
    OrderListView,
    OrderStatusUpdateView,
)

urlpatterns = [
    path("", OrderListView.as_view(), name="order-list"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path(
        "<str:order_number>/cancel/",
        OrderCancelView.as_view(),
        name="order-cancel",
    ),
    path(
        "<str:order_number>/status/",
        OrderStatusUpdateView.as_view(),
        name="order-status",
    ),
    path("<str:order_number>/", OrderDetailView.as_view(), name="order-detail"),
]
