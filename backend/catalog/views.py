from decimal import Decimal, InvalidOperation
import logging
import os

import google.generativeai as genai
from django.db.models import F, Prefetch, Q
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from catalog.models import Brand, Category, Inventory, Product, SubCategory
from catalog.serializers import (
    BrandSerializer,
    CategorySerializer,
    ProductSerializer,
    SubCategorySerializer,
)

logger = logging.getLogger(__name__)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


@api_view(["POST"])
@permission_classes([AllowAny])
def chat_api(request):
    message = request.data.get("message", "")
    if not isinstance(message, str) or not message.strip():
        return Response({"reply": "Please enter a message."}, status=400)

    normalized_message = message.strip()
    matching_products = []
    seen_product_ids = set()
    search_words = dict.fromkeys(
        word.strip(".,!?;:'\"()[]{}")
        for word in normalized_message.split()
        if len(word.strip(".,!?;:'\"()[]{}")) > 3
    )
    for word in search_words:
        matches = Product.objects.filter(
            name__icontains=word,
            is_active=True,
        ).select_related("inventory", "category").order_by("name", "sku")
        for product in matches:
            if product.pk not in seen_product_ids:
                matching_products.append(product)
                seen_product_ids.add(product.pk)
                if len(matching_products) == 5:
                    break
        if len(matching_products) == 5:
            break

    lower_message = normalized_message.lower()
    asks_for_out_of_stock = any(
        phrase in lower_message
        for phrase in ("out of stock", "stock out", "out-of-stock", "unavailable")
    )
    if asks_for_out_of_stock and len(matching_products) < 5:
        out_of_stock = Product.objects.filter(is_active=True).filter(
            Q(inventory__isnull=True)
            | Q(inventory__stock_quantity__lte=F("inventory__reserved_quantity"))
        ).select_related("inventory", "category").order_by("name", "sku")
        for product in out_of_stock:
            if product.pk not in seen_product_ids:
                matching_products.append(product)
                seen_product_ids.add(product.pk)
                if len(matching_products) == 5:
                    break

    product_lines = []
    for product in matching_products:
        try:
            inventory = product.inventory
            available_stock = max(inventory.stock_quantity - inventory.reserved_quantity, 0)
        except Inventory.DoesNotExist:
            available_stock = 0
        product_lines.append(
            f"{product.name} - Rs. {product.selling_price}, "
            f"Stock: {available_stock} available, Category: {product.category.name}"
        )
    product_info = "\n".join(product_lines) or "No matching product found in database"

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return Response({"reply": "Gemini API Key is not configured in .env file"})

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            GEMINI_MODEL,
            system_instruction=(
                "You are FreshBasket AI assistant. Speak in friendly Tanglish "
                "(Tamil + English mix). You are helpful for a grocery and stationery "
                "shop. Use ONLY the given product_info for price and stock. Do NOT "
                "hallucinate price or stock. If product is not found, say politely "
                "it is not available and suggest asking for another product. Answer "
                "any general questions like gift ideas, delivery, offers in a friendly "
                "way."
            ),
        )
        response = model.generate_content(
            f"User question: {normalized_message}\n\n"
            "Available Product Info from Database:\n"
            f"{product_info}\n\nAnswer in Tanglish."
        )
        reply = response.text.strip()
        if reply:
            return Response({"reply": reply})
    except Exception as error:
        logger.error("FreshBasket Gemini request failed (%s).", type(error).__name__)

    reply = "\n".join(product_lines) if product_lines else "Sorry, please try again"
    return Response({"reply": reply})


@api_view(["GET"])
@permission_classes([AllowAny])
def catalog_root(request):
    return Response(
        {
            "categories": "/api/catalog/categories/",
            "subcategories": "/api/catalog/subcategories/",
            "brands": "/api/catalog/brands/",
            "products": "/api/catalog/products/",
        }
    )


class ProductPagination(PageNumberPagination):
    page_size = 20


class CategoryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer

    def get_queryset(self):
        active_subcategories = SubCategory.objects.filter(is_active=True).order_by("name")
        return (
            Category.objects.filter(is_active=True)
            .prefetch_related(Prefetch("subcategories", queryset=active_subcategories))
            .order_by("name")
        )


class SubCategoryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = SubCategorySerializer

    def get_queryset(self):
        queryset = SubCategory.objects.filter(
            is_active=True,
            category__is_active=True,
        ).select_related("category")
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(
                Q(category__slug__iexact=category) | Q(category__name__iexact=category)
            )
        return queryset.order_by("category__name", "name")


class BrandListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = BrandSerializer
    queryset = Brand.objects.filter(is_active=True).order_by("name")


class ProductQuerySetMixin:
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "name",
        "sku",
        "description",
        "short_description",
        "brand__name",
        "category__name",
        "subcategory__name",
    ]
    ordering_fields = ["name", "selling_price", "mrp", "created_at"]
    ordering = ["name", "sku"]

    def get_queryset(self):
        queryset = (
            Product.objects.filter(is_active=True, category__is_active=True)
            .select_related("category", "subcategory", "brand", "inventory")
            .prefetch_related("images")
        )
        params = self.request.query_params

        for parameter, field in (
            ("category", "category"),
            ("subcategory", "subcategory"),
            ("brand", "brand"),
        ):
            value = params.get(parameter)
            if value:
                queryset = queryset.filter(
                    Q(**{f"{field}__slug__iexact": value})
                    | Q(**{f"{field}__name__iexact": value})
                )

        minimum = self._price_parameter(params.get("min_price"), "min_price")
        maximum = self._price_parameter(params.get("max_price"), "max_price")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValidationError({"price": "min_price cannot exceed max_price."})
        if minimum is not None:
            queryset = queryset.filter(selling_price__gte=minimum)
        if maximum is not None:
            queryset = queryset.filter(selling_price__lte=maximum)

        in_stock = self._boolean_parameter(params.get("in_stock"), "in_stock")
        if in_stock is True:
            queryset = queryset.filter(
                inventory__stock_quantity__gt=F("inventory__reserved_quantity")
            )
        elif in_stock is False:
            queryset = queryset.filter(
                Q(inventory__isnull=True)
                | Q(inventory__stock_quantity__lte=F("inventory__reserved_quantity"))
            )

        for parameter, field in (
            ("featured", "is_featured"),
            ("bestseller", "is_bestseller"),
        ):
            value = self._boolean_parameter(params.get(parameter), parameter)
            if value is not None:
                queryset = queryset.filter(**{field: value})

        return queryset

    @staticmethod
    def _price_parameter(value, field_name):
        if value is None:
            return None
        try:
            price = Decimal(value)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValidationError({field_name: "Enter a valid non-negative price."}) from exc
        if not price.is_finite() or price < 0:
            raise ValidationError({field_name: "Enter a valid non-negative price."})
        return price

    @staticmethod
    def _boolean_parameter(value, field_name):
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
        raise ValidationError({field_name: "Use true or false."})


class ProductListView(ProductQuerySetMixin, generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    pagination_class = ProductPagination


class ProductDetailView(ProductQuerySetMixin, generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    lookup_field = "slug"
