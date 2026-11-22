from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from catalog.models import (
    Brand,
    Category,
    Inventory,
    Product,
    ProductImage,
    SubCategory,
)


class ProductModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Vegetables", slug="vegetables")
        cls.other_category = Category.objects.create(name="Fruits", slug="fruits")
        cls.subcategory = SubCategory.objects.create(
            category=cls.category,
            name="Leafy Greens",
            slug="leafy-greens",
        )

    def test_selling_price_cannot_exceed_mrp(self):
        product = Product(
            sku="FB-TEST-001",
            name="Test Spinach",
            slug="test-spinach",
            category=self.category,
            subcategory=self.subcategory,
            unit=Product.Unit.GRAM,
            pack_size="250 g",
            mrp=Decimal("10.00"),
            selling_price=Decimal("11.00"),
        )

        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_subcategory_must_belong_to_product_category(self):
        product = Product(
            sku="FB-TEST-002",
            name="Mismatched Product",
            slug="mismatched-product",
            category=self.other_category,
            subcategory=self.subcategory,
            unit=Product.Unit.PIECE,
            pack_size="1 piece",
            mrp=Decimal("10.00"),
            selling_price=Decimal("10.00"),
        )

        with self.assertRaises(ValidationError) as error:
            product.full_clean()
        self.assertIn("subcategory", error.exception.message_dict)


class PublicCatalogApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name="Vegetables", slug="vegetables")
        subcategory = SubCategory.objects.create(
            category=category,
            name="Leafy Greens",
            slug="leafy-greens",
        )
        brand = Brand.objects.create(name="Fresh Basket", slug="fresh-basket")
        for index in range(21):
            product = Product.objects.create(
                sku=f"FB-API-{index:03d}",
                name=f"Sample Vegetable {index:02d}",
                slug=f"sample-vegetable-{index:02d}",
                category=category,
                subcategory=subcategory,
                brand=brand,
                description="Sample catalogue item.",
                unit=Product.Unit.GRAM,
                pack_size="500 g",
                mrp=Decimal("100.00"),
                selling_price=Decimal("80.00"),
                is_featured=index == 0,
                is_bestseller=index == 1,
            )
            Inventory.objects.create(
                product=product,
                stock_quantity=10 if index else 0,
                reserved_quantity=0,
            )
            if index == 0:
                ProductImage.objects.create(
                    product=product,
                    image_url="https://images.unsplash.com/sample.jpg",
                    alt_text=product.name,
                    is_primary=True,
                )

    def setUp(self):
        self.client = APIClient()

    def test_catalogue_endpoints_are_public_and_products_are_paginated(self):
        catalog_root_response = self.client.get("/api/catalog/")
        products_response = self.client.get("/api/catalog/products/")
        categories_response = self.client.get("/api/catalog/categories/")

        self.assertEqual(catalog_root_response.status_code, 200)
        self.assertEqual(products_response.status_code, 200)
        self.assertEqual(products_response.data["count"], 21)
        self.assertEqual(len(products_response.data["results"]), 20)
        self.assertIsNotNone(products_response.data["next"])
        self.assertEqual(categories_response.status_code, 200)

        product = products_response.data["results"][0]
        self.assertIn("sku", product)
        self.assertIn("category", product)
        self.assertIn("images", product)
        self.assertIn("in_stock", product)

    def test_search_category_price_and_stock_filters(self):
        response = self.client.get(
            "/api/catalog/products/",
            {
                "search": "Sample Vegetable 00",
                "category": "vegetables",
                "min_price": "70",
                "max_price": "90",
                "in_stock": "true",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 9)
        self.assertTrue(all(item["in_stock"] for item in response.data["results"]))

        in_stock = self.client.get(
            "/api/catalog/products/",
            {"category": "vegetables", "in_stock": "true", "featured": "true"},
        )
        self.assertEqual(in_stock.status_code, 200)
        self.assertEqual(in_stock.data["count"], 0)

        available = self.client.get(
            "/api/catalog/products/",
            {"category": "vegetables", "in_stock": "true", "min_price": "80"},
        )
        self.assertEqual(available.status_code, 200)
        self.assertEqual(available.data["count"], 20)

    def test_product_detail_contains_decimal_discount_and_inventory(self):
        response = self.client.get("/api/catalog/products/sample-vegetable-01/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["discount_percentage"], "20.00")
        self.assertEqual(response.data["available_quantity"], 10)
        self.assertTrue(response.data["in_stock"])

    def test_invalid_price_filter_returns_bad_request(self):
        response = self.client.get(
            "/api/catalog/products/",
            {"min_price": "-1"},
        )

        self.assertEqual(response.status_code, 400)
