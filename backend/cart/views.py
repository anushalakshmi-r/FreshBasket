from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Inventory, Product

from cart.models import Cart, CartItem, Wishlist, WishlistItem
from cart.serializers import (
    CartAddSerializer,
    CartQuantitySerializer,
    CartSerializer,
    WishlistAddSerializer,
    WishlistSerializer,
)


def _lock_cart(customer):
    cart, _ = Cart.objects.get_or_create(customer=customer)
    return Cart.objects.select_for_update().get(pk=cart.pk)


def _lock_wishlist(customer):
    wishlist, _ = Wishlist.objects.get_or_create(customer=customer)
    return Wishlist.objects.select_for_update().get(pk=wishlist.pk)


def _loaded_cart(cart_id):
    items = (
        CartItem.objects.select_related("product", "product__brand")
        .prefetch_related("product__images", "product__inventory")
        .order_by("created_at", "id")
    )
    return Cart.objects.prefetch_related(Prefetch("items", queryset=items)).get(pk=cart_id)


def _loaded_wishlist(wishlist_id):
    items = (
        WishlistItem.objects.select_related("product", "product__brand")
        .prefetch_related("product__images", "product__inventory")
        .order_by("created_at", "id")
    )
    return Wishlist.objects.prefetch_related(Prefetch("items", queryset=items)).get(pk=wishlist_id)


def _locked_product(product_id):
    try:
        product = Product.objects.select_for_update().get(pk=product_id)
    except Product.DoesNotExist as exc:
        raise NotFound("Product not found.") from exc
    if not product.is_active:
        raise ValidationError({"product_id": "This product is no longer available."})
    return product


def _available_stock(product):
    inventory = Inventory.objects.select_for_update().filter(product=product).first()
    return inventory.available_quantity if inventory else 0


def _check_stock(product, quantity, available):
    if quantity > available:
        raise ValidationError(
            {
                "detail": f"Only {available} unit(s) of {product.name} are currently available.",
                "available_stock": available,
            }
        )


def _touch_cart(cart):
    Cart.objects.filter(pk=cart.pk).update(updated_at=timezone.now())


def _touch_wishlist(wishlist):
    Wishlist.objects.filter(pk=wishlist.pk).update(updated_at=timezone.now())


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(customer=request.user)
        return Response(CartSerializer(_loaded_cart(cart.pk)).data)


class CartAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CartAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data["product_id"]
        quantity = serializer.validated_data["quantity"]

        with transaction.atomic():
            cart = _lock_cart(request.user)
            product = _locked_product(product_id)
            available = _available_stock(product)
            item = (
                CartItem.objects.select_for_update()
                .filter(cart=cart, product=product)
                .first()
            )
            updated_quantity = quantity + (item.quantity if item else 0)
            _check_stock(product, updated_quantity, available)

            if item:
                item.quantity = updated_quantity
                item.save(update_fields=["quantity", "updated_at"])
                response_status = status.HTTP_200_OK
            else:
                item = CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=updated_quantity,
                )
                response_status = status.HTTP_201_CREATED
            _touch_cart(cart)
            result = _loaded_cart(cart.pk)

        return Response(CartSerializer(result).data, status=response_status)


class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        serializer = CartQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            cart = _lock_cart(request.user)
            item = (
                CartItem.objects.select_for_update()
                .filter(pk=item_id, cart=cart)
                .first()
            )
            if item is None:
                raise NotFound("Cart item not found.")

            product = _locked_product(item.product_id)
            quantity = serializer.validated_data["quantity"]
            _check_stock(product, quantity, _available_stock(product))
            item.quantity = quantity
            item.save(update_fields=["quantity", "updated_at"])
            _touch_cart(cart)
            result = _loaded_cart(cart.pk)

        return Response(CartSerializer(result).data)

    def delete(self, request, item_id):
        with transaction.atomic():
            cart = _lock_cart(request.user)
            item = CartItem.objects.select_for_update().filter(pk=item_id, cart=cart).first()
            if item is None:
                raise NotFound("Cart item not found.")
            item.delete()
            _touch_cart(cart)

        return Response(status=status.HTTP_204_NO_CONTENT)


class CartClearView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        with transaction.atomic():
            cart = _lock_cart(request.user)
            cart.items.all().delete()
            _touch_cart(cart)
            result = _loaded_cart(cart.pk)

        return Response(CartSerializer(result).data)


class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wishlist, _ = Wishlist.objects.get_or_create(customer=request.user)
        return Response(WishlistSerializer(_loaded_wishlist(wishlist.pk)).data)


class WishlistAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WishlistAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            wishlist = _lock_wishlist(request.user)
            product = _locked_product(serializer.validated_data["product_id"])
            _, created = WishlistItem.objects.get_or_create(
                wishlist=wishlist,
                product=product,
            )
            if created:
                _touch_wishlist(wishlist)
            result = _loaded_wishlist(wishlist.pk)

        response_status = (
            status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
        return Response(WishlistSerializer(result).data, status=response_status)


class WishlistItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        with transaction.atomic():
            wishlist = _lock_wishlist(request.user)
            item = (
                WishlistItem.objects.select_for_update()
                .filter(pk=item_id, wishlist=wishlist)
                .first()
            )
            if item is None:
                raise NotFound("Wishlist item not found.")
            item.delete()
            _touch_wishlist(wishlist)

        return Response(status=status.HTTP_204_NO_CONTENT)


class WishlistRemoveProductView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        with transaction.atomic():
            wishlist = _lock_wishlist(request.user)
            deleted_count, _ = WishlistItem.objects.filter(
                wishlist=wishlist,
                product_id=product_id,
            ).delete()
            if deleted_count:
                _touch_wishlist(wishlist)

        return Response(status=status.HTTP_204_NO_CONTENT)
