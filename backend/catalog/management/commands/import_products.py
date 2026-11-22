import csv
import json
import os
import tempfile
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DataError, IntegrityError, transaction
from django.db.models import Q
from django.utils.text import slugify

from catalog.models import Brand, Category, Inventory, Product, ProductImage, SubCategory


REQUIRED_COLUMNS = {
    "sku",
    "name",
    "category",
    "unit",
    "pack_size",
    "mrp",
    "selling_price",
    "dietary_type",
    "stock_quantity",
}

BOOLEAN_VALUES = {
    "true": True,
    "1": True,
    "yes": True,
    "false": False,
    "0": False,
    "no": False,
}


def parse_boolean(value, field_name):
    normalized = (value or "").strip().lower()
    if not normalized:
        return False
    try:
        return BOOLEAN_VALUES[normalized]
    except KeyError as exc:
        raise ValueError(f"{field_name} must be true/false, yes/no, or 1/0.") from exc


def parse_decimal(value, field_name):
    try:
        result = Decimal(value.strip())
    except (AttributeError, InvalidOperation) as exc:
        raise ValueError(f"{field_name} must be a valid decimal amount.") from exc
    if not result.is_finite() or result < 0:
        raise ValueError(f"{field_name} must be a finite, non-negative amount.")
    try:
        return result.quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} is outside the supported precision.") from exc


def parse_stock(value):
    try:
        stock = int(value.strip())
    except (AttributeError, ValueError) as exc:
        raise ValueError("stock_quantity must be a whole number.") from exc
    if stock < 0:
        raise ValueError("stock_quantity cannot be negative.")
    return stock


class Command(BaseCommand):
    help = "Import catalog products and resolve product images through Unsplash."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="catalog/data/products.csv",
            help="CSV file path (relative to the current directory or absolute).",
        )
        parser.add_argument(
            "--image-delay",
            type=float,
            default=0.25,
            help="Seconds to wait between Unsplash image searches (default: 0.25).",
        )
        parser.add_argument(
            "--refresh-images",
            action="store_true",
            help="Search Unsplash again even for rows with a saved Unsplash photo ID.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["file"])
        if not csv_path.is_absolute():
            csv_path = Path.cwd() / csv_path
        if not csv_path.is_file():
            raise CommandError(f"CSV file not found: {csv_path}")

        if options["image_delay"] < 0:
            raise CommandError("--image-delay cannot be negative.")

        api_key = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()
        if not api_key:
            raise CommandError(
                "UNSPLASH_ACCESS_KEY is not configured. Set it in backend/.env."
            )

        try:
            with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
                reader = csv.DictReader(source)
                if reader.fieldnames is None:
                    raise CommandError("The CSV file is empty or has no header row.")
                columns = {name.strip() for name in reader.fieldnames if name}
                missing_columns = sorted(REQUIRED_COLUMNS - columns)
                if missing_columns:
                    raise CommandError(
                        "CSV is missing required columns: " + ", ".join(missing_columns)
                    )
                rows = list(reader)
                fieldnames = reader.fieldnames
            self._resolve_unsplash_images(
                rows,
                csv_path,
                api_key,
                options["image_delay"],
                options["refresh_images"],
                fieldnames,
            )
            self._import_rows(rows)
        except UnicodeError as exc:
            raise CommandError("CSV must be readable UTF-8 text.") from exc
        except csv.Error as exc:
            raise CommandError(f"Could not parse CSV: {exc}") from exc

    def _resolve_unsplash_images(
        self, rows, csv_path, api_key, delay, refresh_images, fieldnames
    ):
        """Fill missing image URLs from Unsplash and checkpoint each result to CSV."""
        output_fields = list(fieldnames)
        if "unsplash_photo_id" not in output_fields:
            output_fields.append("unsplash_photo_id")

        used_photo_ids = {
            row.get("unsplash_photo_id", "").strip()
            for row in rows
            if row.get("unsplash_photo_id", "").strip()
        }
        pending = [
            row
            for row in rows
            if refresh_images or not row.get("unsplash_photo_id", "").strip()
        ]
        self.stdout.write(
            f"Resolving Unsplash images for {len(pending)} of {len(rows)} products..."
        )

        for index, row in enumerate(pending, start=1):
            photo_id, image_url = self._search_unsplash(
                row["name"], row.get("category", ""), api_key, used_photo_ids
            )
            row["image_url"] = image_url
            row["alt_text"] = row["name"]
            row["unsplash_photo_id"] = photo_id
            used_photo_ids.add(photo_id)
            self._write_csv_checkpoint(csv_path, output_fields, rows)
            self.stdout.write(f"[{index}/{len(pending)}] Image saved for {row['name']}")
            if index < len(pending) and delay:
                time.sleep(delay)

    def _search_unsplash(self, product_name, category, api_key, used_photo_ids):
        search_queries = [product_name]
        if category:
            search_queries.append(f"{product_name} {category.replace('-', ' ')}")
        search_queries.append(f"fresh {product_name}")
        search_queries.extend(
            word
            for word in product_name.split()
            if len(word) > 3 and word.lower() not in {query.lower() for query in search_queries}
        )

        for search_query in search_queries:
            for page in range(1, 4):
                query = urlencode(
                    {
                        "query": search_query,
                        "page": page,
                        "per_page": 30,
                        "content_filter": "high",
                    }
                )
                request = Request(
                    f"https://api.unsplash.com/search/photos?{query}",
                    headers={
                        "Authorization": f"Client-ID {api_key}",
                        "Accept-Version": "v1",
                        "Accept": "application/json",
                    },
                )
                try:
                    with urlopen(request, timeout=30) as response:
                        payload = json.loads(response.read().decode("utf-8"))
                except HTTPError as exc:
                    remaining_requests = exc.headers.get("X-Ratelimit-Remaining", "")
                    if exc.code == 429 or (
                        exc.code == 403 and remaining_requests == "0"
                    ):
                        retry_after = exc.headers.get("Retry-After", "")
                        wait_message = (
                            f" Retry-After: {retry_after} seconds."
                            if retry_after.isdigit()
                            else ""
                        )
                        raise CommandError(
                            "Unsplash rate limit reached while searching for "
                            f"'{product_name}'. Completed image URLs are saved in the CSV; "
                            f"rerun the importer later.{wait_message}"
                        ) from exc
                    if exc.code in (401, 403):
                        raise CommandError(
                            "Unsplash rejected the access key. Check UNSPLASH_ACCESS_KEY "
                            "and the key's API permissions."
                        ) from exc
                    raise CommandError(
                        f"Unsplash returned HTTP {exc.code} while searching for '{product_name}'."
                    ) from exc
                except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                    raise CommandError(
                        f"Could not complete Unsplash search for '{product_name}': {exc}"
                    ) from exc

                for photo in payload.get("results", []):
                    image_url = (photo.get("urls") or {}).get("regular")
                    photo_id = photo.get("id")
                    if image_url and photo_id and photo_id not in used_photo_ids:
                        return photo_id, image_url
                if not payload.get("results"):
                    break

        raise CommandError(
            f"Unsplash returned no unused photo for '{product_name}'. "
            "No product data was imported; try again or review the search results."
        )

    @staticmethod
    def _write_csv_checkpoint(csv_path, fieldnames, rows):
        """Persist progress atomically so a rate limit can be resumed later."""
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                newline="",
                dir=csv_path.parent,
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                writer = csv.DictWriter(
                    temporary_file,
                    fieldnames=fieldnames,
                    extrasaction="ignore",
                )
                writer.writeheader()
                writer.writerows(rows)
            os.replace(temporary_path, csv_path)
        finally:
            if temporary_path and temporary_path.exists():
                temporary_path.unlink()

    def _import_rows(self, rows):
        summary = {
            "created": 0,
            "updated": 0,
            "inventories_created": 0,
            "images_created": 0,
            "failed": 0,
        }
        errors = []

        with transaction.atomic():
            for line_number, raw_row in enumerate(rows, start=2):
                sku = ""
                try:
                    if None in raw_row:
                        raise ValueError("Row has more values than the CSV header.")
                    row = {
                        (key.strip() if key else ""): (value.strip() if value else "")
                        for key, value in raw_row.items()
                    }
                    sku = row.get("sku", "").upper()
                    with transaction.atomic():
                        counts = self._import_row(row, sku)
                    summary["created" if counts["product_created"] else "updated"] += 1
                    summary["inventories_created"] += counts["inventory_created"]
                    summary["images_created"] += counts["image_created"]
                except (
                    IntegrityError,
                    DataError,
                    ValidationError,
                    ValueError,
                ) as exc:
                    summary["failed"] += 1
                    message = str(exc)
                    errors.append(f"Row {line_number} (SKU {sku or 'missing'}): {message}")

        self.stdout.write(
            "Import summary: "
            f"{summary['created']} products created, "
            f"{summary['updated']} products updated, "
            f"{summary['inventories_created']} inventory records created, "
            f"{summary['images_created']} product images created, "
            f"{summary['failed']} rows failed."
        )
        for error in errors:
            self.stderr.write(self.style.ERROR(error))
        if errors:
            raise CommandError(
                f"Import completed with {summary['failed']} invalid row(s); "
                "valid rows were committed. See errors above."
            )

    def _import_row(self, row, sku):
        for field in REQUIRED_COLUMNS:
            if not row.get(field):
                raise ValueError(f"Required field '{field}' is empty.")

        category = Category.objects.filter(
            Q(slug__iexact=row["category"]) | Q(name__iexact=row["category"])
        ).first()
        if category is None:
            raise ValueError(f"Unknown category '{row['category']}'. Run seed_categories first.")

        subcategory = None
        subcategory_value = row.get("subcategory", "")
        if subcategory_value:
            subcategory = SubCategory.objects.filter(category=category).filter(
                Q(slug__iexact=subcategory_value) | Q(name__iexact=subcategory_value)
            ).first()
            if subcategory is None:
                raise ValueError(
                    f"Unknown subcategory '{subcategory_value}' for category '{category.name}'."
                )

        brand = None
        brand_name = row.get("brand", "")
        if brand_name:
            brand_slug = slugify(brand_name)
            brand, _ = Brand.objects.get_or_create(
                name=brand_name,
                defaults={"slug": brand_slug},
            )

        unit = row["unit"].lower()
        if unit not in Product.Unit.values:
            raise ValueError(
                f"unit must be one of: {', '.join(Product.Unit.values)}."
            )

        dietary_type = row["dietary_type"].lower()
        if dietary_type not in Product.DietaryType.values:
            raise ValueError(
                "dietary_type must be one of: "
                f"{', '.join(Product.DietaryType.values)}."
            )

        mrp = parse_decimal(row["mrp"], "mrp")
        selling_price = parse_decimal(row["selling_price"], "selling_price")
        stock_quantity = parse_stock(row["stock_quantity"])
        if selling_price > mrp:
            raise ValueError("selling_price cannot exceed mrp.")

        values = {
            "name": row["name"],
            "slug": f"{slugify(row['name'])}-{slugify(sku)}"[:240],
            "category": category,
            "subcategory": subcategory,
            "brand": brand,
            "description": row.get("description", ""),
            "short_description": row.get("short_description", ""),
            "unit": unit,
            "pack_size": row["pack_size"],
            "mrp": mrp,
            "selling_price": selling_price,
            "dietary_type": dietary_type,
            "is_featured": parse_boolean(row.get("is_featured", ""), "is_featured"),
            "is_bestseller": parse_boolean(row.get("is_bestseller", ""), "is_bestseller"),
            "is_active": parse_boolean(row.get("is_active") or "true", "is_active"),
        }

        product = Product.objects.filter(sku=sku).first()
        product_created = product is None
        if product is None:
            product = Product(sku=sku, **values)
        else:
            for field, value in values.items():
                setattr(product, field, value)
        product.full_clean()
        product.save()

        inventory_defaults = {"stock_quantity": stock_quantity}
        inventory_created = False
        if not Inventory.objects.filter(product=product).exists():
            inventory_candidate = Inventory(product=product, **inventory_defaults)
            inventory_candidate.full_clean()
            _, inventory_created = Inventory.objects.get_or_create(
                product=product,
                defaults=inventory_defaults,
            )

        image_created = 0
        image_url = row.get("image_url", "")
        if image_url:
            alt_text = row.get("alt_text") or product.name
            ProductImage.objects.filter(
                product=product,
                is_primary=True,
            ).exclude(image_url=image_url).update(is_primary=False)
            image, image_created = ProductImage.objects.get_or_create(
                product=product,
                image_url=image_url,
                defaults={"alt_text": alt_text, "is_primary": True},
            )
            if not image_created and (
                image.alt_text != alt_text or not image.is_primary
            ):
                image.alt_text = alt_text
                image.is_primary = True
                image.full_clean()
                image.save(update_fields=["alt_text", "is_primary"])

        return {
            "product_created": product_created,
            "inventory_created": int(inventory_created),
            "image_created": int(image_created),
        }
