from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="subcategories",
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"],
                name="catalog_unique_subcategory_name",
            ),
            models.UniqueConstraint(
                fields=["category", "slug"],
                name="catalog_unique_subcategory_slug",
            ),
        ]
        verbose_name_plural = "subcategories"

    def __str__(self):
        return f"{self.category.name} / {self.name}"


class Brand(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    logo_url = models.URLField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    class Unit(models.TextChoices):
        KILOGRAM = "kg", "Kilogram"
        GRAM = "g", "Gram"
        LITRE = "litre", "Litre"
        MILLILITRE = "ml", "Millilitre"
        PIECE = "piece", "Piece"
        PACK = "pack", "Pack"

    class DietaryType(models.TextChoices):
        VEGETARIAN = "vegetarian", "Vegetarian"
        NON_VEGETARIAN = "non_vegetarian", "Non-vegetarian"
        NOT_APPLICABLE = "not_applicable", "Not applicable"

    sku = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=240, unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        related_name="products",
        blank=True,
        null=True,
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        related_name="products",
        blank=True,
        null=True,
    )
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    unit = models.CharField(max_length=10, choices=Unit.choices)
    pack_size = models.CharField(max_length=80)
    mrp = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    dietary_type = models.CharField(
        max_length=20,
        choices=DietaryType.choices,
        default=DietaryType.NOT_APPLICABLE,
    )
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "sku"]
        indexes = [
            models.Index(fields=["category", "is_active"], name="catalog_prod_cat_active"),
            models.Index(fields=["subcategory", "is_active"], name="catalog_prod_sub_active"),
            models.Index(fields=["brand", "is_active"], name="catalog_prod_brand_active"),
            models.Index(
                fields=["is_active", "is_featured", "is_bestseller"],
                name="catalog_prod_flags",
            ),
            models.Index(fields=["selling_price"], name="catalog_prod_price"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(mrp__gte=0),
                name="catalog_product_mrp_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(selling_price__gte=0),
                name="catalog_product_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(selling_price__lte=models.F("mrp")),
                name="catalog_product_price_lte_mrp",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.mrp is not None and self.mrp < 0:
            errors["mrp"] = "MRP cannot be negative."
        if self.selling_price is not None and self.selling_price < 0:
            errors["selling_price"] = "Selling price cannot be negative."
        if (
            self.mrp is not None
            and self.selling_price is not None
            and self.selling_price > self.mrp
        ):
            errors["selling_price"] = "Selling price cannot exceed MRP."
        if (
            self.subcategory_id
            and self.category_id
            and self.subcategory.category_id != self.category_id
        ):
            errors["subcategory"] = "Subcategory must belong to the selected category."
        if errors:
            raise ValidationError(errors)

    @property
    def discount_percentage(self):
        if not self.mrp:
            return Decimal("0.00")
        return ((self.mrp - self.selling_price) * Decimal("100") / self.mrp).quantize(
            Decimal("0.01")
        )

    @property
    def available_quantity(self):
        try:
            inventory = self.inventory
        except Inventory.DoesNotExist:
            return 0
        return max(inventory.stock_quantity - inventory.reserved_quantity, 0)

    def save(self, *args, **kwargs):
        if not self.slug and self.name and self.sku:
            self.slug = f"{slugify(self.name)}-{slugify(self.sku)}"[:240]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.sku})"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image_url = models.URLField(max_length=500)
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "image_url"],
                name="catalog_unique_product_image",
            ),
        ]

    def __str__(self):
        return f"Image for {self.product.sku}"


class Inventory(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="inventory",
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(stock_quantity__gte=0),
                name="catalog_stock_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(reserved_quantity__gte=0),
                name="catalog_reserved_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(low_stock_threshold__gte=0),
                name="catalog_threshold_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(reserved_quantity__lte=models.F("stock_quantity")),
                name="catalog_reserved_lte_stock",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.stock_quantity < 0:
            errors["stock_quantity"] = "Stock quantity cannot be negative."
        if self.reserved_quantity < 0:
            errors["reserved_quantity"] = "Reserved quantity cannot be negative."
        if self.low_stock_threshold < 0:
            errors["low_stock_threshold"] = "Low-stock threshold cannot be negative."
        if self.reserved_quantity > self.stock_quantity:
            errors["reserved_quantity"] = "Reserved quantity cannot exceed stock quantity."
        if errors:
            raise ValidationError(errors)

    @property
    def available_quantity(self):
        return max(self.stock_quantity - self.reserved_quantity, 0)

    def __str__(self):
        return f"Inventory for {self.product.sku}"
