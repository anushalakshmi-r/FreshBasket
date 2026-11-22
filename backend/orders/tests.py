from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import DatabaseError
from rest_framework.test import APIClient, APITestCase

from accounts.models import CustomerAddress
from cart.models import Cart, CartItem
from catalog.models import Category, Inventory, Product
from orders.models import Order
from orders.services import create_order

User = get_user_model()


class CheckoutAndOrderApiTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="checkout-customer",
            email="checkout@example.test",
            password="test-password-only",
        )
        self.other_customer = User.objects.create_user(
            username="other-checkout-customer",
            email="other-checkout@example.test",
            password="test-password-only",
        )
        self.staff = User.objects.create_user(
            username="order-staff",
            email="staff@example.test",
            password="test-password-only",
            is_staff=True,
        )
        self.category = Category.objects.create(name="Test Groceries", slug="test-groceries")
        self.product = Product.objects.create(
            sku="TEST-001",
            name="Test Rice",
            slug="test-rice",
            category=self.category,
            unit=Product.Unit.PACK,
            pack_size="1 pack",
            mrp=Decimal("120.00"),
            selling_price=Decimal("100.00"),
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            stock_quantity=10,
            reserved_quantity=2,
        )
        self.cart = Cart.objects.create(customer=self.customer)
        self.other_cart = Cart.objects.create(customer=self.other_customer)
        self.address = self.make_address(self.customer)
        self.other_address = self.make_address(self.other_customer, city="Mumbai")
        self.client.force_authenticate(user=self.customer)

    def make_address(self, customer, city="Pune"):
        return CustomerAddress.objects.create(
            customer=customer,
            full_name="Test Customer",
            phone_number="+919876543210",
            address_line_1="12 Market Road",
            city=city,
            state="Maharashtra",
            postal_code="411001" if city == "Pune" else "400001",
        )

    def add_to_cart(self, quantity=2, product=None):
        return CartItem.objects.create(
            cart=self.cart,
            product=product or self.product,
            quantity=quantity,
        )

    def checkout(self, address_id=None, payment_method="cod"):
        return self.client.post(
            "/api/orders/checkout/",
            {
                "address_id": address_id or self.address.pk,
                "payment_method": payment_method,
            },
            format="json",
        )

    def test_checkout_uses_database_totals_snapshots_and_deducts_stock_once(self):
        self.add_to_cart(quantity=3)
        quote = self.client.get("/api/orders/checkout/")
        self.assertEqual(quote.status_code, 200)
        self.assertEqual(quote.data["subtotal"], Decimal("300.00"))
        self.assertEqual(quote.data["delivery_fee"], Decimal("40.00"))
        self.assertEqual(quote.data["grand_total"], Decimal("340.00"))

        response = self.checkout()
        self.assertEqual(response.status_code, 201)
        order = Order.objects.get(order_number=response.data["order_number"])
        item = order.items.get()
        self.assertEqual(order.subtotal, Decimal("300.00"))
        self.assertEqual(order.grand_total, Decimal("340.00"))
        self.assertEqual(order.payment_method, Order.PaymentMethod.COD)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(order.order_status, Order.OrderStatus.PENDING)
        self.assertEqual(item.product_name_snapshot, "Test Rice")
        self.assertEqual(item.sku_snapshot, "TEST-001")
        self.assertEqual(item.unit_price, Decimal("100.00"))
        self.assertEqual(item.line_total, Decimal("300.00"))
        self.assertEqual(order.delivery_address_snapshot["city"], "Pune")
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 0)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 7)
        self.assertEqual(self.inventory.reserved_quantity, 2)

        self.product.name = "Renamed Rice"
        self.product.selling_price = Decimal("110.00")
        self.product.save()
        item.refresh_from_db()
        self.assertEqual(item.product_name_snapshot, "Test Rice")
        self.assertEqual(item.unit_price, Decimal("100.00"))

    def test_online_payment_remains_pending_and_one_customer_cannot_read_another_order(self):
        self.add_to_cart(quantity=1)
        response = self.checkout(payment_method="online")
        self.assertEqual(response.status_code, 201)
        order_number = response.data["order_number"]
        self.assertEqual(response.data["payment_status"], Order.PaymentStatus.PENDING)

        other_client = APIClient()
        other_client.force_authenticate(user=self.other_customer)
        self.assertEqual(other_client.get("/api/orders/").data, [])
        self.assertEqual(other_client.get(f"/api/orders/{order_number}/").status_code, 404)

    def test_delivery_is_free_at_the_documented_threshold(self):
        self.product.selling_price = Decimal("499.00")
        self.product.mrp = Decimal("500.00")
        self.product.save(update_fields=["selling_price", "mrp"])
        self.add_to_cart(quantity=1)

        quote = self.client.get("/api/orders/checkout/")
        self.assertEqual(quote.status_code, 200)
        self.assertEqual(quote.data["subtotal"], Decimal("499.00"))
        self.assertEqual(quote.data["delivery_fee"], Decimal("0.00"))
        self.assertEqual(quote.data["grand_total"], Decimal("499.00"))

    def test_checkout_rejects_empty_cart_foreign_address_and_insufficient_stock(self):
        empty_response = self.checkout()
        self.assertEqual(empty_response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

        self.add_to_cart()
        foreign_address = self.checkout(address_id=self.other_address.pk)
        self.assertEqual(foreign_address.status_code, 400)
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 1)

        CartItem.objects.filter(cart=self.cart).update(quantity=9)
        insufficient = self.checkout()
        self.assertEqual(insufficient.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 10)
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 1)

    def test_inactive_product_and_unauthenticated_checkout_are_rejected(self):
        self.add_to_cart()
        self.product.is_active = False
        self.product.save(update_fields=["is_active"])
        response = self.checkout()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/api/orders/checkout/").status_code, 401)

    def test_failed_order_item_creation_rolls_back_order_stock_and_cart(self):
        self.add_to_cart()
        with patch("orders.services.OrderItem.objects.create", side_effect=DatabaseError):
            with self.assertRaises(DatabaseError):
                create_order(
                    customer=self.customer,
                    address_id=self.address.pk,
                    payment_method=Order.PaymentMethod.COD,
                )

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 1)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 10)

    def test_cancellation_restores_stock_once_and_admin_status_is_restricted(self):
        self.add_to_cart(quantity=3)
        response = self.checkout()
        order_number = response.data["order_number"]
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 7)

        cancelled = self.client.post(f"/api/orders/{order_number}/cancel/")
        self.assertEqual(cancelled.status_code, 200)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 10)
        repeated = self.client.post(f"/api/orders/{order_number}/cancel/")
        self.assertEqual(repeated.status_code, 400)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 10)

        staff_client = APIClient()
        staff_client.force_authenticate(user=self.staff)
        transition = staff_client.patch(
            f"/api/orders/{order_number}/status/",
            {"order_status": "confirmed"},
            format="json",
        )
        self.assertEqual(transition.status_code, 400)
        self.assertEqual(transition.data["detail"], "Cannot move an order from cancelled to confirmed.")

        self.client.force_authenticate(user=self.other_customer)
        self.assertEqual(
            self.client.post(f"/api/orders/{order_number}/cancel/").status_code,
            404,
        )

    def test_admin_can_advance_order_status_but_customer_cannot(self):
        self.add_to_cart()
        order_number = self.checkout().data["order_number"]
        denied = self.client.patch(
            f"/api/orders/{order_number}/status/",
            {"order_status": "confirmed"},
            format="json",
        )
        self.assertEqual(denied.status_code, 403)

        staff_client = APIClient()
        staff_client.force_authenticate(user=self.staff)
        confirmed = staff_client.patch(
            f"/api/orders/{order_number}/status/",
            {"order_status": "confirmed"},
            format="json",
        )
        self.assertEqual(confirmed.status_code, 200)
        self.assertEqual(confirmed.data["order_status"], "confirmed")

    def test_customer_cannot_cancel_after_order_enters_processing(self):
        self.add_to_cart(quantity=3)
        order_number = self.checkout().data["order_number"]
        staff_client = APIClient()
        staff_client.force_authenticate(user=self.staff)
        for next_status in ("confirmed", "processing"):
            response = staff_client.patch(
                f"/api/orders/{order_number}/status/",
                {"order_status": next_status},
                format="json",
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(f"/api/orders/{order_number}/cancel/")
        self.assertEqual(response.status_code, 400)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 7)
