from django.urls import path

from accounts.views import (
    CsrfTokenView,
    CustomerAddressDetailView,
    CustomerAddressListCreateView,
    CustomerAddressSetDefaultView,
    CustomerProfileView,
    LoginView,
    LogoutView,
    RegisterView,
    TokenRefreshCookieView,
)

urlpatterns = [
    path("csrf/", CsrfTokenView.as_view(), name="csrf-token"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshCookieView.as_view(), name="token-refresh"),
    path("profile/", CustomerProfileView.as_view(), name="profile"),
    path("addresses/", CustomerAddressListCreateView.as_view(), name="address-list"),
    path(
        "addresses/<int:address_id>/",
        CustomerAddressDetailView.as_view(),
        name="address-detail",
    ),
    path(
        "addresses/<int:address_id>/set-default/",
        CustomerAddressSetDefaultView.as_view(),
        name="address-set-default",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
]
