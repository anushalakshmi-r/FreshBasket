from decimal import Decimal

from rest_framework import serializers

from catalog.models import (
    Brand,
    Category,
    Inventory,
    Product,
    ProductImage,
    SubCategory,
)


class CategoryBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class SubCategoryBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ["id", "name", "slug"]


class BrandBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "slug", "logo_url"]


class SubCategorySerializer(serializers.ModelSerializer):
    category = CategoryBriefSerializer(read_only=True)

    class Meta:
        model = SubCategory
        fields = [
            "id",
            "category",
            "name",
            "slug",
            "description",
            "image_url",
            "is_active",
        ]


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategoryBriefSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image_url",
            "is_active",
            "created_at",
            "updated_at",
            "subcategories",
        ]


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "slug", "logo_url", "description", "is_active"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image_url", "alt_text", "is_primary"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategoryBriefSerializer(read_only=True)
    subcategory = SubCategoryBriefSerializer(read_only=True)
    brand = BrandBriefSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    discount_percentage = serializers.SerializerMethodField()
    stock_quantity = serializers.SerializerMethodField()
    reserved_quantity = serializers.SerializerMethodField()
    available_quantity = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "slug",
            "category",
            "subcategory",
            "brand",
            "description",
            "short_description",
            "unit",
            "pack_size",
            "mrp",
            "selling_price",
            "discount_percentage",
            "dietary_type",
            "images",
            "stock_quantity",
            "reserved_quantity",
            "available_quantity",
            "in_stock",
            "is_featured",
            "is_bestseller",
            "created_at",
            "updated_at",
        ]

    def _inventory(self, product):
        try:
            return product.inventory
        except Inventory.DoesNotExist:
            return None

    def get_discount_percentage(self, product):
        if not product.mrp:
            return "0.00"
        percentage = (
            (product.mrp - product.selling_price) * Decimal("100") / product.mrp
        ).quantize(Decimal("0.01"))
        return format(percentage, ".2f")

    def get_stock_quantity(self, product):
        inventory = self._inventory(product)
        return inventory.stock_quantity if inventory else 0

    def get_reserved_quantity(self, product):
        inventory = self._inventory(product)
        return inventory.reserved_quantity if inventory else 0

    def get_available_quantity(self, product):
        inventory = self._inventory(product)
        return inventory.available_quantity if inventory else 0

    def get_in_stock(self, product):
        return self.get_available_quantity(product) > 0
