from django.contrib.auth import get_user_model
from django.urls import path
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter

from catalog.models import Category, Inventory, Product
from orders.models import Coupon, Order

User = get_user_model()


class CategoryAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class CouponAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = "__all__"


class CategoryAdminViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategoryAdminSerializer
    permission_classes = [IsAdminUser]


class ProductAdminViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category", "inventory").all()
    serializer_class = ProductAdminSerializer
    permission_classes = [IsAdminUser]


class CouponAdminViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponAdminSerializer
    permission_classes = [IsAdminUser]


@api_view(["GET"])
@permission_classes([IsAdminUser])
def dashboard(request):
    orders = Order.objects.all()
    return Response({
        "total_sales": orders.filter(payment_status=Order.PaymentStatus.PAID).aggregate(value=Sum("grand_total"))["value"] or 0,
        "total_orders": orders.count(),
        "total_customers": User.objects.filter(is_staff=False).count(),
        "total_products": Product.objects.filter(is_active=True).count(),
        "pending_orders": orders.filter(order_status__in=["pending", "confirmed", "processing", "packed", "shipped", "out_for_delivery"]).count(),
        "completed_orders": orders.filter(order_status=Order.OrderStatus.DELIVERED).count(),
        "cancelled_orders": orders.filter(order_status=Order.OrderStatus.CANCELLED).count(),
        "low_stock_products": Inventory.objects.filter(stock_quantity__lte=__import__("django.db.models", fromlist=["F"]).F("low_stock_threshold")).count(),
        "recent_orders": list(orders.values("order_number", "grand_total", "order_status", "created_at")[:10]),
    })


router = DefaultRouter()
router.register("categories", CategoryAdminViewSet, basename="admin-category")
router.register("products", ProductAdminViewSet, basename="admin-product")
router.register("coupons", CouponAdminViewSet, basename="admin-coupon")
urlpatterns = [*router.urls]
urlpatterns += [path("dashboard/", dashboard, name="admin-dashboard")]
