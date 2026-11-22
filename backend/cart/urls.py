from django.urls import path

from cart.views import (
    CartAddView,
    CartClearView,
    CartItemDetailView,
    CartView,
)

urlpatterns = [
    path("", CartView.as_view(), name="cart"),
    path("add/", CartAddView.as_view(), name="cart-add"),
    path("items/<int:item_id>/", CartItemDetailView.as_view(), name="cart-item-detail"),
    path("clear/", CartClearView.as_view(), name="cart-clear"),
]
