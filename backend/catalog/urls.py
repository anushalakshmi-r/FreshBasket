from django.urls import path

from catalog.views import (
    BrandListView,
    CategoryListView,
    ProductDetailView,
    ProductListView,
    SubCategoryListView,
    chat_api,
    catalog_root,
)

app_name = "catalog"

urlpatterns = [
    path("api/chat/", chat_api, name="chat-api-catalog-alias"),
    path("", catalog_root, name="catalog-root"),
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("subcategories/", SubCategoryListView.as_view(), name="subcategory-list"),
    path("brands/", BrandListView.as_view(), name="brand-list"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),
]
