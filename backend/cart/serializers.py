from decimal import Decimal

from rest_framework import serializers

from catalog.models import Inventory, Product

from cart.models import Cart, CartItem, Wishlist, WishlistItem


class ShoppingProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    brand_name = serializers.CharField(source="brand.name", read_only=True, default="")
    discount_percentage = serializers.SerializerMethodField()
    available_stock = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "image_url",
            "brand_name",
            "pack_size",
            "selling_price",
            "mrp",
            "discount_percentage",
            "available_stock",
            "in_stock",
            "is_active",
        ]

    def get_image_url(self, product):
        images = list(product.images.all())
        primary_image = next((image for image in images if image.is_primary), None)
        image = primary_image or (images[0] if images else None)
        return image.image_url if image else ""

    def get_discount_percentage(self, product):
        return format(product.discount_percentage, ".2f")

    def get_available_stock(self, product):
        try:
            return product.inventory.available_quantity
        except Inventory.DoesNotExist:
            return 0

    def get_in_stock(self, product):
        return self.get_available_stock(product) > 0


class CartItemSerializer(serializers.ModelSerializer):
    product = ShoppingProductSerializer(read_only=True)
    item_subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "item_subtotal"]

    def get_item_subtotal(self, item):
        subtotal = item.product.selling_price * item.quantity
        return format(subtotal.quantize(Decimal("0.01")), ".2f")


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "items", "item_count", "total", "created_at", "updated_at"]

    def get_total(self, cart):
        total = sum(
            (item.product.selling_price * item.quantity for item in cart.items.all()),
            Decimal("0.00"),
        )
        return format(total.quantize(Decimal("0.01")), ".2f")

    def get_item_count(self, cart):
        return sum(item.quantity for item in cart.items.all())


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ShoppingProductSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "created_at"]


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "items", "created_at", "updated_at"]


class CartAddSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)


class CartQuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class WishlistAddSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
