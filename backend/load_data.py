"""Load the cleaned application fixture once, without blocking deploys on one bad row."""

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import django

django.setup()

from django.apps import apps
from django.core import serializers
from django.core.serializers.base import DeserializationError
from django.db import DatabaseError, IntegrityError, transaction


FIXTURE_PATH = Path(__file__).resolve().parent / "full_backup.json"
MODEL_ORDER = (
    "auth.user",
    "catalog.category",
    "catalog.subcategory",
    "catalog.brand",
    "accounts.customerprofile",
    "accounts.customeraddress",
    "catalog.product",
    "catalog.productimage",
    "catalog.inventory",
    "cart.cart",
    "cart.cartitem",
    "cart.wishlist",
    "cart.wishlistitem",
    "orders.order",
    "orders.orderitem",
    "payments.payment",
    "payments.webhookevent",
)


def main():
    if not FIXTURE_PATH.is_file():
        raise FileNotFoundError(f"Required fixture not found at {FIXTURE_PATH}.")

    objects = json.loads(FIXTURE_PATH.read_text(encoding="utf-8-sig"))
    model_order = {label: index for index, label in enumerate(MODEL_ORDER)}
    objects = [
        item
        for item in objects
        if item.get("model") in model_order and "pk" in item
    ]
    objects.sort(key=lambda item: (model_order[item["model"]], item["pk"]))

    if not objects:
        print("Fixture contains no supported application objects; no data loaded.")
        return 0

    if any(
        apps.get_model(*label.split("."))._default_manager.exists()
        for label in MODEL_ORDER
        if apps.get_model(*label.split(".")) is not None
    ):
        print("Application data already exists; fixture loading skipped.")
        return 0

    loaded = 0
    failed = 0
    for index, item in enumerate(objects, start=1):
        try:
            with transaction.atomic():
                deserialized = serializers.deserialize(
                    "json",
                    json.dumps([item]),
                    ignorenonexistent=True,
                )
                for fixture_object in deserialized:
                    fixture_object.save()
                    loaded += 1
        except (DeserializationError, DatabaseError, IntegrityError, ValueError) as error:
            failed += 1
            print(
                f"Skipping fixture object {index} ({item.get('model')} "
                f"pk={item.get('pk')}): {type(error).__name__}",
                file=sys.stderr,
            )
        except Exception as error:  # Keep a malformed legacy object from failing deployment.
            failed += 1
            print(
                f"Skipping fixture object {index} ({item.get('model')} "
                f"pk={item.get('pk')}): {type(error).__name__}",
                file=sys.stderr,
            )

    print(
        f"Fixture load complete: {loaded} objects loaded, "
        f"{failed} objects skipped after errors."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
