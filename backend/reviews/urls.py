from django.urls import path

from reviews.views import ProductReviewDetailView, ProductReviewListCreateView

urlpatterns = [
    path("products/<int:product_id>/", ProductReviewListCreateView.as_view(), name="product-reviews"),
    path("<int:review_id>/", ProductReviewDetailView.as_view(), name="review-detail"),
]
