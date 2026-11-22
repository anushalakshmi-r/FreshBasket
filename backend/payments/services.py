import hashlib
import hmac
import json
import logging
import secrets
from decimal import Decimal

import razorpay
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from requests.exceptions import RequestException
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from razorpay.errors import (
    BadRequestError,
    GatewayError,
    ServerError,
    SignatureVerificationError,
)

from orders.models import Order
from payments.models import Payment, WebhookEvent

logger = logging.getLogger(__name__)
PAYMENT_API_ERRORS = (BadRequestError, GatewayError, ServerError, RequestException)


class PaymentConfigurationError(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Razorpay is not configured. Add the backend Razorpay test credentials."
    default_code = "payment_not_configured"


class PaymentGatewayError(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "Razorpay could not complete the request. Please retry."
    default_code = "payment_gateway_unavailable"


class PaymentConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This order is not eligible for this payment action."
    default_code = "payment_conflict"


class WebhookConfigurationError(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Razorpay webhook verification is not configured."
    default_code = "webhook_not_configured"


def _client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise PaymentConfigurationError()
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def _locked_owned_order(customer, order_number):
    order_id = (
        Order.objects.filter(customer=customer, order_number=order_number)
        .values_list("pk", flat=True)
        .first()
    )
    if order_id is None:
        raise NotFound("Order not found.")
    return Order.objects.select_for_update().get(pk=order_id)


def _eligible_online_order(order):
    if order.payment_method != Order.PaymentMethod.ONLINE:
        raise PaymentConflict("Only online orders can use Razorpay.")
    if order.order_status == Order.OrderStatus.CANCELLED:
        raise PaymentConflict("A cancelled order cannot be paid.")
    if order.payment_status == Order.PaymentStatus.PAID:
        raise PaymentConflict("This order has already been paid.")
    if order.payment_status not in (
        Order.PaymentStatus.PENDING,
        Order.PaymentStatus.FAILED,
    ):
        raise PaymentConflict("This order is not eligible for payment.")


def create_razorpay_order(*, customer, order_number):
    with transaction.atomic():
        order = _locked_owned_order(customer, order_number)
        _eligible_online_order(order)
        if order.payment_attempts.filter(
            payment_status=Payment.Status.CAPTURED
        ).exists():
            raise PaymentConflict("This order already has a successful payment.")

        pending_attempt = (
            Payment.objects.select_for_update()
            .filter(order=order, payment_status=Payment.Status.CREATED)
            .order_by("-created_at", "-pk")
            .first()
        )
        if pending_attempt:
            return pending_attempt, False

        authorized_attempt = (
            Payment.objects.select_for_update()
            .filter(order=order, payment_status=Payment.Status.AUTHORIZED)
            .order_by("-created_at", "-pk")
            .first()
        )
        if authorized_attempt:
            raise PaymentConflict(
                "A payment is authorized and awaiting capture. Please check the order again shortly."
            )

        amount_paise = int((order.grand_total * Decimal("100")).quantize(Decimal("1")))
        client = _client()
        receipt = f"{order.order_number}-{secrets.token_hex(4)}"
        try:
            gateway_order = client.order.create(
                {
                    "amount": amount_paise,
                    "currency": "INR",
                    "receipt": receipt,
                    "notes": {"freshbasket_order_number": order.order_number},
                }
            )
        except PAYMENT_API_ERRORS as error:
            logger.warning(
                "Razorpay order creation failed for FreshBasket order %s.",
                order.order_number,
            )
            raise PaymentGatewayError() from error

        gateway_order_id = gateway_order.get("id")
        if (
            not isinstance(gateway_order_id, str)
            or not gateway_order_id
            or gateway_order.get("amount") != amount_paise
            or gateway_order.get("currency") != "INR"
        ):
            logger.error(
                "Razorpay returned an invalid order response for order %s.",
                order.order_number,
            )
            raise PaymentGatewayError("Razorpay returned an invalid order response.")

        payment = Payment.objects.create(
            order=order,
            razorpay_order_id=gateway_order_id,
            amount=order.grand_total,
            currency="INR",
        )
        if order.payment_status == Order.PaymentStatus.FAILED:
            order.payment_status = Order.PaymentStatus.PENDING
            order.save(update_fields=["payment_status", "updated_at"])
        return payment, True


def _validate_gateway_payment(gateway_payment, *, payment_id, razorpay_order_id, amount):
    if (
        not isinstance(gateway_payment, dict)
        or gateway_payment.get("id") != payment_id
        or gateway_payment.get("order_id") != razorpay_order_id
        or gateway_payment.get("currency") != "INR"
    ):
        raise PaymentGatewayError("Razorpay returned payment details that did not match this order.")
    try:
        gateway_amount = int(gateway_payment.get("amount"))
    except (TypeError, ValueError) as error:
        raise PaymentGatewayError("Razorpay returned an invalid payment amount.") from error
    expected_amount = int((amount * Decimal("100")).quantize(Decimal("1")))
    if gateway_amount != expected_amount:
        raise PaymentGatewayError("Razorpay returned a payment amount that did not match this order.")


def _find_order_for_razorpay_order(razorpay_order_id):
    order_id = (
        Payment.objects.filter(razorpay_order_id=razorpay_order_id)
        .values_list("order_id", flat=True)
        .first()
    )
    if order_id is None:
        raise NotFound("Payment order not found.")
    return Order.objects.select_for_update().get(pk=order_id)


def _resolve_payment_attempt(order, razorpay_order_id, payment_id):
    payment = (
        Payment.objects.select_for_update()
        .filter(
            order=order,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=payment_id,
        )
        .first()
    )
    if payment:
        return payment

    payment = (
        Payment.objects.select_for_update()
        .filter(
            order=order,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id__isnull=True,
        )
        .order_by("-created_at", "-pk")
        .first()
    )
    if payment:
        payment.razorpay_payment_id = payment_id
        return payment

    return Payment(
        order=order,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=payment_id,
        amount=order.grand_total,
        currency="INR",
    )


def _persist_payment_state(
    *,
    order,
    payment,
    gateway_payment,
    signature_verified,
):
    state = gateway_payment.get("status")
    payment_id = gateway_payment["id"]
    existing_payment_ids = Payment.objects.filter(razorpay_payment_id=payment_id)
    if payment.pk:
        existing_payment_ids = existing_payment_ids.exclude(pk=payment.pk)
    conflicting_payment = existing_payment_ids.exists()
    if conflicting_payment:
        raise PaymentConflict("This Razorpay payment is already linked to another payment attempt.")

    payment.signature_verified = payment.signature_verified or signature_verified
    payment.payment_method = gateway_payment.get("method", "")[:30]
    if state == "captured":
        payment.razorpay_payment_id = payment_id
        if payment.payment_status == Payment.Status.CAPTURED:
            payment.save(
                update_fields=[
                    "razorpay_payment_id",
                    "signature_verified",
                    "payment_method",
                    "updated_at",
                ]
            )
            return "captured"
        if payment.payment_status == Payment.Status.REFUND_REQUIRED:
            return Payment.Status.REFUND_REQUIRED
        if (
            order.order_status == Order.OrderStatus.CANCELLED
            or order.payment_status == Order.PaymentStatus.PAID
        ):
            payment.payment_status = Payment.Status.REFUND_REQUIRED
            payment.save()
            return "refund_required"

        payment.payment_status = Payment.Status.CAPTURED
        payment.save()
        order.payment_status = Order.PaymentStatus.PAID
        if order.order_status == Order.OrderStatus.PENDING:
            order.order_status = Order.OrderStatus.CONFIRMED
        order.save(update_fields=["payment_status", "order_status", "updated_at"])
        return "captured"

    if payment.payment_status in (
        Payment.Status.CAPTURED,
        Payment.Status.REFUND_REQUIRED,
    ):
        return payment.payment_status

    if state == "failed":
        payment.razorpay_payment_id = payment_id
        payment.payment_status = (
            Payment.Status.CANCELLED
            if order.order_status == Order.OrderStatus.CANCELLED
            else Payment.Status.FAILED
        )
        payment.save()
        if (
            order.order_status != Order.OrderStatus.CANCELLED
            and order.payment_status != Order.PaymentStatus.PAID
        ):
            order.payment_status = Order.PaymentStatus.FAILED
            order.save(update_fields=["payment_status", "updated_at"])
        return "failed"

    if state == "authorized":
        if order.order_status == Order.OrderStatus.CANCELLED:
            payment.payment_status = Payment.Status.CANCELLED
        else:
            payment.payment_status = Payment.Status.AUTHORIZED
        payment.razorpay_payment_id = payment_id
        payment.save()
        return payment.payment_status

    if order.order_status == Order.OrderStatus.CANCELLED:
        payment.payment_status = Payment.Status.CANCELLED
        payment.razorpay_payment_id = payment_id
        payment.save()
        return "cancelled"

    payment.payment_status = Payment.Status.CREATED
    payment.razorpay_payment_id = payment_id
    payment.save()
    return "pending"


def verify_checkout_payment(
    *,
    customer,
    razorpay_order_id,
    razorpay_payment_id,
    razorpay_signature="",
):
    client = _client()
    with transaction.atomic():
        order = _find_order_for_razorpay_order(razorpay_order_id)
        if order.customer_id != customer.pk:
            raise NotFound("Payment order not found.")
        if order.payment_method != Order.PaymentMethod.ONLINE:
            raise PaymentConflict("Only online orders can use Razorpay.")

        payment = _resolve_payment_attempt(
            order,
            razorpay_order_id,
            razorpay_payment_id,
        )
        if (
            payment.razorpay_payment_id == razorpay_payment_id
            and payment.payment_status == Payment.Status.CAPTURED
            and payment.signature_verified
        ):
            return order, payment, "captured"

        if razorpay_signature:
            try:
                client.utility.verify_payment_signature(
                    {
                        "razorpay_order_id": razorpay_order_id,
                        "razorpay_payment_id": razorpay_payment_id,
                        "razorpay_signature": razorpay_signature,
                    }
                )
            except SignatureVerificationError as error:
                raise ValidationError(
                    {"detail": "Razorpay payment signature is invalid."}
                ) from error

        try:
            gateway_payment = client.payment.fetch(razorpay_payment_id)
        except PAYMENT_API_ERRORS as error:
            logger.warning(
                "Razorpay payment lookup failed for FreshBasket order %s.",
                order.order_number,
            )
            raise PaymentGatewayError("Razorpay could not verify the payment. Please retry.") from error

        _validate_gateway_payment(
            gateway_payment,
            payment_id=razorpay_payment_id,
            razorpay_order_id=razorpay_order_id,
            amount=order.grand_total,
        )
        gateway_status = gateway_payment.get("status")
        if not razorpay_signature and gateway_status != "failed":
            raise ValidationError(
                {"detail": "A valid Razorpay checkout signature is required for successful payments."}
            )

        if (
            order.order_status == Order.OrderStatus.CANCELLED
            and gateway_status != "captured"
        ):
            payment.razorpay_payment_id = razorpay_payment_id
            payment.payment_status = Payment.Status.CANCELLED
            payment.save(update_fields=["razorpay_payment_id", "payment_status", "updated_at"])
            return order, payment, "cancelled"

        state = _persist_payment_state(
            order=order,
            payment=payment,
            gateway_payment=gateway_payment,
            signature_verified=bool(razorpay_signature),
        )
        return order, payment, state


def verify_webhook_signature(raw_body, signature):
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    if not secret:
        raise WebhookConfigurationError()
    if not isinstance(signature, str) or len(signature) != 64 or not signature.isascii():
        return False
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


def process_webhook(*, event_id, payload):
    event_type = payload.get("event", "")
    if not isinstance(event_type, str) or not event_type:
        raise ValidationError({"detail": "Razorpay webhook event type is missing."})
    event_payload = payload.get("payload")
    payment_data = event_payload.get("payment") if isinstance(event_payload, dict) else None
    payment_entity = payment_data.get("entity") if isinstance(payment_data, dict) else None
    if not isinstance(payment_entity, dict):
        payment_entity = {}

    if event_type in ("payment.captured", "payment.authorized", "payment.failed"):
        razorpay_order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")
        if not razorpay_order_id or not payment_id:
            raise ValidationError({"detail": "Razorpay webhook payment identifiers are missing."})

    try:
        with transaction.atomic():
            event = WebhookEvent.objects.create(
                event_id=event_id,
                event_type=event_type[:80],
            )
            if event_type not in ("payment.captured", "payment.authorized", "payment.failed"):
                event.processed_at = timezone.now()
                event.save(update_fields=["processed_at"])
                return "ignored"

            order = _find_order_for_razorpay_order(razorpay_order_id)
            payment = _resolve_payment_attempt(order, razorpay_order_id, payment_id)
            gateway_payment = {
                "id": payment_id,
                "order_id": razorpay_order_id,
                "amount": payment_entity.get("amount"),
                "currency": payment_entity.get("currency"),
                "status": payment_entity.get("status"),
                "method": payment_entity.get("method", ""),
            }
            _validate_gateway_payment(
                gateway_payment,
                payment_id=payment_id,
                razorpay_order_id=razorpay_order_id,
                amount=order.grand_total,
            )
            expected_status = {
                "payment.captured": "captured",
                "payment.authorized": "authorized",
                "payment.failed": "failed",
            }[event_type]
            if gateway_payment["status"] != expected_status:
                raise ValidationError(
                    {"detail": "Razorpay webhook event does not match the payment status."}
                )
            if order.payment_method != Order.PaymentMethod.ONLINE:
                raise PaymentConflict("A Razorpay event cannot update a non-online order.")
            _persist_payment_state(
                order=order,
                payment=payment,
                gateway_payment=gateway_payment,
                signature_verified=True,
            )
            event.payment = payment
            event.processed_at = timezone.now()
            event.save(update_fields=["payment", "processed_at"])
            return "processed"
    except IntegrityError:
        if WebhookEvent.objects.filter(event_id=event_id).exists():
            return "duplicate"
        raise


def webhook_event_id(raw_body, header_event_id):
    if header_event_id:
        if len(header_event_id) > 255:
            raise ValidationError({"detail": "Razorpay event ID is too long."})
        return header_event_id
    return f"sha256:{hashlib.sha256(raw_body).hexdigest()}"


def parse_webhook_body(raw_body):
    try:
        payload = json.loads(raw_body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError({"detail": "Razorpay webhook body is not valid JSON."}) from error
    if not isinstance(payload, dict):
        raise ValidationError({"detail": "Razorpay webhook body must be a JSON object."})
    return payload
