from django.contrib import admin
from django.urls import include, path

from config.api_views import api_root, health_check
from catalog.views import chat_api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/chat/", chat_api, name="chat-api"),
    path("api/accounts/", include("accounts.urls")),
    path("api/catalog/", include("catalog.urls")),
    path("api/cart/", include("cart.urls")),
    path("api/wishlist/", include("cart.wishlist_urls")),
    path("api/orders/", include("orders.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/", api_root, name="api-root"),
    path("api/health/", health_check, name="health-check"),
]
