from django.contrib import admin

from catalog.models import Brand, Category, Inventory, Product, ProductImage, SubCategory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    ordering = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "slug", "is_active"]
    list_filter = ["category", "is_active"]
    search_fields = ["name", "slug", "category__name"]
    ordering = ["category__name", "name"]
    autocomplete_fields = ["category"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    ordering = ["name"]
    prepopulated_fields = {"slug": ("name",)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class InventoryInline(admin.StackedInline):
    model = Inventory
    extra = 0
    max_num = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "sku",
        "category",
        "brand",
        "selling_price",
        "mrp",
        "stock_quantity",
        "is_active",
        "is_featured",
        "is_bestseller",
    ]
    list_filter = [
        "category",
        "subcategory",
        "brand",
        "dietary_type",
        "is_active",
        "is_featured",
        "is_bestseller",
    ]
    search_fields = ["name", "sku", "slug", "category__name", "brand__name"]
    ordering = ["name", "sku"]
    autocomplete_fields = ["category", "subcategory", "brand"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ProductImageInline, InventoryInline]
    list_select_related = ["category", "subcategory", "brand", "inventory"]

    @admin.display(description="Stock", ordering="inventory__stock_quantity")
    def stock_quantity(self, obj):
        try:
            return obj.inventory.stock_quantity
        except Inventory.DoesNotExist:
            return 0


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ["product", "image_url", "is_primary"]
    list_filter = ["is_primary"]
    search_fields = ["product__name", "product__sku", "alt_text"]
    autocomplete_fields = ["product"]
    ordering = ["product__name", "-is_primary"]


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "stock_quantity",
        "reserved_quantity",
        "available_quantity",
        "low_stock_threshold",
        "updated_at",
    ]
    list_filter = ["updated_at"]
    search_fields = ["product__name", "product__sku"]
    autocomplete_fields = ["product"]
    ordering = ["product__name"]
    readonly_fields = ["updated_at"]
