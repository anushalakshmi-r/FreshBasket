from django.contrib import admin
from django.urls import include, path

from config.api_views import api_root, health_check
from catalog.views import (
    BrandListView,
    CategoryListView,
    ProductDetailView,
    ProductListView,
    SubCategoryListView,
    chat_api,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/chat/", chat_api, name="chat-api"),
    path("api/categories/", CategoryListView.as_view(), name="public-category-list"),
    path("api/subcategories/", SubCategoryListView.as_view(), name="public-subcategory-list"),
    path("api/brands/", BrandListView.as_view(), name="public-brand-list"),
    path("api/products/", ProductListView.as_view(), name="public-product-list"),
    path(
        "api/products/<slug:slug>/",
        ProductDetailView.as_view(),
        name="public-product-detail",
    ),
    path("api/accounts/", include("accounts.urls")),
    path("api/catalog/", include("catalog.urls")),
    path("api/cart/", include("cart.urls")),
    path("api/wishlist/", include("cart.wishlist_urls")),
    path("api/orders/", include("orders.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/", api_root, name="api-root"),
    path("api/health/", health_check, name="health-check"),
]
