from decimal import Decimal

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from catalog.models import Category, Inventory, Product
from cart.models import Cart, CartItem, Wishlist, WishlistItem


class ShoppingApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.customer = user_model.objects.create_user(
            username="basket-customer",
            email="basket@example.test",
            password="test-password-only",
        )
        self.other_customer = user_model.objects.create_user(
            username="other-customer",
            email="other@example.test",
            password="test-password-only",
        )
        self.category = Category.objects.create(
            name="Test groceries",
            slug="test-groceries",
        )
        self.product = self.create_product(
            sku="TEST-001",
            slug="test-product",
            stock=5,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.customer)

    def create_product(self, sku, slug, stock=5, is_active=True):
        product = Product.objects.create(
            sku=sku,
            name=f"Product {sku}",
            slug=slug,
            category=self.category,
            unit=Product.Unit.PIECE,
            pack_size="1 piece",
            mrp=Decimal("12.00"),
            selling_price=Decimal("10.00"),
            is_active=is_active,
        )
        Inventory.objects.create(
            product=product,
            stock_quantity=stock,
            reserved_quantity=0,
        )
        return product

    def test_cart_requires_authentication_and_returns_database_totals(self):
        anonymous_client = APIClient()
        self.assertIn(anonymous_client.get("/api/cart/").status_code, [401, 403])

        response = self.client.get("/api/cart/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["items"], [])
        self.assertEqual(response.data["total"], "0.00")

        response = self.client.post(
            "/api/cart/add/",
            {"product_id": self.product.pk, "quantity": 2},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["item_count"], 2)
        self.assertEqual(response.data["total"], "20.00")
        self.assertEqual(response.data["items"][0]["product"]["sku"], "TEST-001")
        self.assertEqual(response.data["items"][0]["item_subtotal"], "20.00")

    def test_duplicate_additions_update_quantity_and_reject_insufficient_stock(self):
        url = "/api/cart/add/"
        first = self.client.post(
            url,
            {"product_id": self.product.pk, "quantity": 2},
            format="json",
        )
        second = self.client.post(
            url,
            {"product_id": self.product.pk, "quantity": 2},
            format="json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["items"][0]["quantity"], 4)
        self.assertEqual(CartItem.objects.count(), 1)

        insufficient = self.client.post(
            url,
            {"product_id": self.product.pk, "quantity": 2},
            format="json",
        )
        self.assertEqual(insufficient.status_code, 400)
        self.assertEqual(int(insufficient.data["available_stock"]), 5)
        self.assertEqual(CartItem.objects.get().quantity, 4)
        patch_insufficient = self.client.patch(
            f"/api/cart/items/{second.data['items'][0]['id']}/",
            {"quantity": 6},
            format="json",
        )
        self.assertEqual(patch_insufficient.status_code, 400)
        self.assertEqual(CartItem.objects.get().quantity, 4)

    def test_cart_update_remove_clear_and_customer_isolation(self):
        added = self.client.post(
            "/api/cart/add/",
            {"product_id": self.product.pk, "quantity": 2},
            format="json",
        )
        item_id = added.data["items"][0]["id"]

        updated = self.client.patch(
            f"/api/cart/items/{item_id}/",
            {"quantity": 3},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["total"], "30.00")

        other_client = APIClient()
        other_client.force_authenticate(user=self.other_customer)
        self.assertEqual(other_client.get("/api/cart/").data["items"], [])
        self.assertEqual(
            other_client.patch(
                f"/api/cart/items/{item_id}/",
                {"quantity": 1},
                format="json",
            ).status_code,
            404,
        )
        self.assertEqual(
            other_client.delete(f"/api/cart/items/{item_id}/").status_code,
            404,
        )

        self.assertEqual(
            self.client.delete(f"/api/cart/items/{item_id}/").status_code,
            204,
        )
        self.client.post(
            "/api/cart/add/",
            {"product_id": self.product.pk, "quantity": 1},
            format="json",
        )
        cleared = self.client.delete("/api/cart/clear/")
        self.assertEqual(cleared.status_code, 200)
        self.assertEqual(cleared.data["items"], [])
        self.assertEqual(cleared.data["total"], "0.00")

    def test_inactive_products_are_rejected_for_cart_and_wishlist(self):
        inactive_product = self.create_product(
            sku="TEST-002",
            slug="inactive-product",
            is_active=False,
        )
        cart_response = self.client.post(
            "/api/cart/add/",
            {"product_id": inactive_product.pk, "quantity": 1},
            format="json",
        )
        wishlist_response = self.client.post(
            "/api/wishlist/add/",
            {"product_id": inactive_product.pk},
            format="json",
        )
        self.assertEqual(cart_response.status_code, 400)
        self.assertEqual(wishlist_response.status_code, 400)

    def test_wishlist_is_deduplicated_and_isolated_between_customers(self):
        anonymous_client = APIClient()
        self.assertIn(anonymous_client.get("/api/wishlist/").status_code, [401, 403])

        url = "/api/wishlist/add/"
        first = self.client.post(url, {"product_id": self.product.pk}, format="json")
        second = self.client.post(url, {"product_id": self.product.pk}, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(WishlistItem.objects.count(), 1)

        item_id = second.data["items"][0]["id"]
        other_client = APIClient()
        other_client.force_authenticate(user=self.other_customer)
        self.assertEqual(other_client.get("/api/wishlist/").data["items"], [])
        self.assertEqual(
            other_client.delete(f"/api/wishlist/items/{item_id}/").status_code,
            404,
        )
        self.assertEqual(
            self.client.delete(f"/api/wishlist/items/{item_id}/").status_code,
            204,
        )
        self.assertEqual(WishlistItem.objects.count(), 0)
        self.client.post(url, {"product_id": self.product.pk}, format="json")
        self.assertEqual(
            self.client.delete(
                f"/api/wishlist/remove-product/{self.product.pk}/"
            ).status_code,
            204,
        )
        self.assertEqual(self.client.get("/api/wishlist/").data["items"], [])

    def test_shopping_models_are_registered_in_admin(self):
        for model in (Cart, CartItem, Wishlist, WishlistItem):
            with self.subTest(model=model.__name__):
                self.assertIn(model, admin.site._registry)
