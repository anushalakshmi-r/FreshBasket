from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from catalog.models import Category, Product
from reviews.models import ProductReview


class ProductReviewApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="reviewer", email="reviewer@example.com", password="Strong-pass-123")
        category = Category.objects.create(name="Review category", slug="review-category")
        self.product = Product.objects.create(sku="REV-1", name="Review product", slug="review-product", category=category, unit="piece", pack_size="1", mrp=10, selling_price=10)
        self.url = f"/api/reviews/products/{self.product.pk}/"

    def test_authenticated_customer_can_create_once_and_read_summary(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, {"rating": 5, "title": "Fresh", "body": "Excellent."}, format="json")
        self.assertEqual(response.status_code, 201)
        duplicate = self.client.post(self.url, {"rating": 4, "body": "Again."}, format="json")
        self.assertEqual(duplicate.status_code, 400)
        summary = self.client.get(self.url)
        self.assertEqual(summary.data["review_count"], 1)
        self.assertEqual(summary.data["average_rating"], 5.0)
        self.assertEqual(ProductReview.objects.count(), 1)
