from django.contrib import admin

from cart.models import Cart, CartItem, Wishlist, WishlistItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    autocomplete_fields = ("product",)


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    autocomplete_fields = ("product",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("customer", "created_at", "updated_at")
    search_fields = ("customer__email", "customer__username")
    ordering = ("-updated_at",)
    autocomplete_fields = ("customer",)
    inlines = (CartItemInline,)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("customer", "created_at", "updated_at")
    search_fields = ("customer__email", "customer__username")
    ordering = ("-updated_at",)
    autocomplete_fields = ("customer",)
    inlines = (WishlistItemInline,)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("product", "cart", "quantity", "created_at", "updated_at")
    search_fields = (
        "product__name",
        "product__sku",
        "cart__customer__email",
        "cart__customer__username",
    )
    list_filter = ("product__category", "created_at")
    ordering = ("-updated_at",)
    autocomplete_fields = ("cart", "product")


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("product", "wishlist", "created_at")
    search_fields = (
        "product__name",
        "product__sku",
        "wishlist__customer__email",
        "wishlist__customer__username",
    )
    list_filter = ("product__category", "created_at")
    ordering = ("-created_at",)
    autocomplete_fields = ("wishlist", "product")
