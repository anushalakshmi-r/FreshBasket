import hashlib
import hmac
import json
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient, APITestCase
from razorpay.errors import SignatureVerificationError

from catalog.models import Category, Inventory, Product
from orders.models import Order, OrderItem
from payments.models import Payment, WebhookEvent

User = get_user_model()


@override_settings(
    RAZORPAY_KEY_ID="rzp_test_public",
    RAZORPAY_KEY_SECRET="test-secret",
    RAZORPAY_WEBHOOK_SECRET="webhook-test-secret",
)
class PaymentApiTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="payment-customer",
            email="payment-customer@example.test",
            password="test-password-only",
        )
        self.other_customer = User.objects.create_user(
            username="other-payment-customer",
            email="other-payment-customer@example.test",
            password="test-password-only",
        )
        category = Category.objects.create(name="Payment groceries", slug="payment-groceries")
        self.product = Product.objects.create(
            sku="PAYMENT-001",
            name="Payment test rice",
            slug="payment-test-rice",
            category=category,
            unit=Product.Unit.PACK,
            pack_size="1 pack",
            mrp=Decimal("300.00"),
            selling_price=Decimal("300.00"),
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            stock_quantity=9,
            reserved_quantity=0,
        )
        self.order = self.make_order()
        self.client.force_authenticate(user=self.customer)

    def make_order(self, payment_method=Order.PaymentMethod.ONLINE):
        order = Order.objects.create(
            customer=self.customer,
            delivery_address_snapshot={"city": "Pune"},
            subtotal=Decimal("300.00"),
            delivery_fee=Decimal("40.00"),
            discount=Decimal("0.00"),
            grand_total=Decimal("340.00"),
            payment_method=payment_method,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name_snapshot=self.product.name,
            sku_snapshot=self.product.sku,
            unit_price=Decimal("300.00"),
            quantity=1,
            line_total=Decimal("300.00"),
        )
        return order

    def fake_client(self, *, status="captured", amount=34000, payment_id="pay_test_1"):
        return SimpleNamespace(
            order=SimpleNamespace(
                create=Mock(
                    return_value={
                        "id": "order_test_1",
                        "amount": 34000,
                        "currency": "INR",
                    }
                )
            ),
            utility=SimpleNamespace(verify_payment_signature=Mock()),
            payment=SimpleNamespace(
                fetch=Mock(
                    return_value={
                        "id": payment_id,
                        "order_id": "order_test_1",
                        "amount": amount,
                        "currency": "INR",
                        "status": status,
                        "method": "upi",
                    }
                )
            ),
        )

    def create_payment_order(self, order=None):
        return self.client.post(
            "/api/payments/create-order/",
            {"order_number": (order or self.order).order_number},
            format="json",
        )

    def test_create_payment_order_uses_order_total_and_enforces_ownership(self):
        client = self.fake_client()
        with patch("payments.services.razorpay.Client", return_value=client):
            response = self.client.post(
                "/api/payments/create-order/",
                {"order_number": self.order.order_number, "amount": 1},
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["amount"], 34000)
        self.assertEqual(response.data["key_id"], "rzp_test_public")
        client.order.create.assert_called_once()
        self.assertEqual(client.order.create.call_args.args[0]["amount"], 34000)

        other_client = APIClient()
        other_client.force_authenticate(user=self.other_customer)
        self.assertEqual(
            other_client.post(
                "/api/payments/create-order/",
                {"order_number": self.order.order_number},
                format="json",
            ).status_code,
            404,
        )

    def test_verified_payment_marks_order_paid_once_without_deducting_inventory_again(self):
        with patch(
            "payments.services.razorpay.Client",
            return_value=self.fake_client(),
        ):
            created = self.create_payment_order()
        self.assertEqual(created.status_code, 201)
        client = self.fake_client()
        request_data = {
            "razorpay_order_id": "order_test_1",
            "razorpay_payment_id": "pay_test_1",
            "razorpay_signature": "verified-signature",
        }
        with patch("payments.services.razorpay.Client", return_value=client):
            response = self.client.post(
                "/api/payments/verify/",
                request_data,
                format="json",
            )
            duplicate = self.client.post(
                "/api/payments/verify/",
                request_data,
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(duplicate.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.order.order_status, Order.OrderStatus.CONFIRMED)
        self.assertEqual(self.order.payment_attempts.count(), 1)
        payment = self.order.payment_attempts.get()
        self.assertEqual(payment.payment_status, Payment.Status.CAPTURED)
        self.assertTrue(payment.signature_verified)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 9)

    def test_invalid_signature_and_wrong_amount_never_mark_order_paid(self):
        with patch(
            "payments.services.razorpay.Client",
            return_value=self.fake_client(),
        ):
            created = self.create_payment_order()
        self.assertEqual(created.status_code, 201)
        client = self.fake_client()
        client.utility.verify_payment_signature.side_effect = SignatureVerificationError(
            "Invalid signature"
        )
        with patch("payments.services.razorpay.Client", return_value=client):
            invalid_signature = self.client.post(
                "/api/payments/verify/",
                {
                    "razorpay_order_id": "order_test_1",
                    "razorpay_payment_id": "pay_test_1",
                    "razorpay_signature": "wrong",
                },
                format="json",
            )
        self.assertEqual(invalid_signature.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)

        client = self.fake_client(amount=33999)
        with patch("payments.services.razorpay.Client", return_value=client):
            wrong_amount = self.client.post(
                "/api/payments/verify/",
                {
                    "razorpay_order_id": "order_test_1",
                    "razorpay_payment_id": "pay_test_1",
                    "razorpay_signature": "valid",
                },
                format="json",
            )
        self.assertEqual(wrong_amount.status_code, 502)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)

    def test_verified_failure_allows_a_new_attempt_and_cancelled_orders_cannot_be_paid(self):
        first_client = self.fake_client(status="failed")
        first_client.order.create.return_value = {
            "id": "order_test_1",
            "amount": 34000,
            "currency": "INR",
        }
        with patch("payments.services.razorpay.Client", return_value=first_client):
            self.assertEqual(self.create_payment_order().status_code, 201)
            failed = self.client.post(
                "/api/payments/verify/",
                {
                    "razorpay_order_id": "order_test_1",
                    "razorpay_payment_id": "pay_test_1",
                },
                format="json",
            )
        self.assertEqual(failed.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.FAILED)
        self.assertEqual(self.order.payment_attempts.get().payment_status, Payment.Status.FAILED)

        second_client = self.fake_client()
        second_client.order.create.return_value = {
            "id": "order_test_2",
            "amount": 34000,
            "currency": "INR",
        }
        with patch("payments.services.razorpay.Client", return_value=second_client):
            retry = self.create_payment_order()
        self.assertEqual(retry.status_code, 201)
        self.assertEqual(retry.data["razorpay_order_id"], "order_test_2")
        self.assertEqual(self.order.payment_attempts.count(), 2)

        self.order.order_status = Order.OrderStatus.CANCELLED
        self.order.save(update_fields=["order_status", "updated_at"])
        self.assertEqual(self.create_payment_order().status_code, 409)

    def test_webhook_signature_and_event_id_make_capture_idempotent(self):
        Payment.objects.create(
            order=self.order,
            razorpay_order_id="order_test_1",
            amount=self.order.grand_total,
            currency="INR",
        )
        payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_1",
                        "order_id": "order_test_1",
                        "amount": 34000,
                        "currency": "INR",
                        "status": "captured",
                        "method": "upi",
                    }
                }
            },
        }
        raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(
            b"webhook-test-secret",
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        headers = {
            "HTTP_X_RAZORPAY_SIGNATURE": signature,
            "HTTP_X_RAZORPAY_EVENT_ID": "evt_test_capture",
            "content_type": "application/json",
        }

        first = self.client.generic("POST", "/api/payments/webhook/", raw_body, **headers)
        duplicate = self.client.generic("POST", "/api/payments/webhook/", raw_body, **headers)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["status"], "processed")
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(duplicate.data["status"], "duplicate")
        self.assertEqual(WebhookEvent.objects.count(), 1)

        repeated_delivery = self.client.generic(
            "POST",
            "/api/payments/webhook/",
            raw_body,
            HTTP_X_RAZORPAY_SIGNATURE=signature,
            HTTP_X_RAZORPAY_EVENT_ID="evt_test_capture_redelivered",
            content_type="application/json",
        )
        self.assertEqual(repeated_delivery.status_code, 200)
        self.assertEqual(
            self.order.payment_attempts.get().payment_status,
            Payment.Status.CAPTURED,
        )

        duplicate_payment_payload = {
            **payload,
            "payload": {
                "payment": {
                    "entity": {
                        **payload["payload"]["payment"]["entity"],
                        "id": "pay_test_duplicate",
                    }
                }
            },
        }
        duplicate_payment_body = json.dumps(
            duplicate_payment_payload,
            separators=(",", ":"),
        ).encode("utf-8")
        duplicate_payment_signature = hmac.new(
            b"webhook-test-secret",
            duplicate_payment_body,
            hashlib.sha256,
        ).hexdigest()
        duplicate_capture = self.client.generic(
            "POST",
            "/api/payments/webhook/",
            duplicate_payment_body,
            HTTP_X_RAZORPAY_SIGNATURE=duplicate_payment_signature,
            HTTP_X_RAZORPAY_EVENT_ID="evt_test_second_capture",
            content_type="application/json",
        )
        self.assertEqual(duplicate_capture.status_code, 200)
        self.assertEqual(
            self.order.payment_attempts.get(
                razorpay_payment_id="pay_test_duplicate"
            ).payment_status,
            Payment.Status.REFUND_REQUIRED,
        )
        self.assertEqual(WebhookEvent.objects.count(), 3)

        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)

        invalid = self.client.generic(
            "POST",
            "/api/payments/webhook/",
            raw_body,
            HTTP_X_RAZORPAY_SIGNATURE="invalid",
            content_type="application/json",
        )
        self.assertEqual(invalid.status_code, 400)

    def test_late_capture_after_cancellation_requires_reconciliation(self):
        Payment.objects.create(
            order=self.order,
            razorpay_order_id="order_test_1",
            amount=self.order.grand_total,
            currency="INR",
            payment_status=Payment.Status.CANCELLED,
        )
        self.order.order_status = Order.OrderStatus.CANCELLED
        self.order.save(update_fields=["order_status", "updated_at"])
        payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_late",
                        "order_id": "order_test_1",
                        "amount": 34000,
                        "currency": "INR",
                        "status": "captured",
                    }
                }
            },
        }
        raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(
            b"webhook-test-secret",
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        response = self.client.generic(
            "POST",
            "/api/payments/webhook/",
            raw_body,
            HTTP_X_RAZORPAY_SIGNATURE=signature,
            HTTP_X_RAZORPAY_EVENT_ID="evt_test_late_capture",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(self.order.order_status, Order.OrderStatus.CANCELLED)
        payment = self.order.payment_attempts.get()
        self.assertEqual(payment.payment_status, Payment.Status.REFUND_REQUIRED)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 9)

    def test_missing_credentials_unauthenticated_and_cod_requests_are_rejected(self):
        with override_settings(RAZORPAY_KEY_ID="", RAZORPAY_KEY_SECRET=""):
            unavailable = self.create_payment_order()
        self.assertEqual(unavailable.status_code, 503)

        self.client.force_authenticate(user=None)
        self.assertEqual(
            self.client.post(
                "/api/payments/create-order/",
                {"order_number": self.order.order_number},
                format="json",
            ).status_code,
            401,
        )

        cod_order = self.make_order(payment_method=Order.PaymentMethod.COD)
        self.client.force_authenticate(user=self.customer)
        self.assertEqual(self.create_payment_order(cod_order).status_code, 409)
        self.assertEqual(cod_order.payment_status, Order.PaymentStatus.PENDING)

    def test_payment_status_is_customer_scoped(self):
        self.assertEqual(
            self.client.get(f"/api/payments/order/{self.order.order_number}/").status_code,
            200,
        )
        other_client = APIClient()
        other_client.force_authenticate(user=self.other_customer)
        self.assertEqual(
            other_client.get(f"/api/payments/order/{self.order.order_number}/").status_code,
            404,
        )
