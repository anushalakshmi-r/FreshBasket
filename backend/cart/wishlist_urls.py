from django.urls import path

from cart.views import (
    WishlistAddView,
    WishlistItemDetailView,
    WishlistRemoveProductView,
    WishlistView,
)

urlpatterns = [
    path("", WishlistView.as_view(), name="wishlist"),
    path("add/", WishlistAddView.as_view(), name="wishlist-add"),
    path("items/<int:item_id>/", WishlistItemDetailView.as_view(), name="wishlist-item-detail"),
    path(
        "remove-product/<int:product_id>/",
        WishlistRemoveProductView.as_view(),
        name="wishlist-remove-product",
    ),
]
