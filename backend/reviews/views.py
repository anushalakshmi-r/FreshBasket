from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Product
from reviews.models import ProductReview
from reviews.serializers import ProductReviewSerializer


class ProductReviewListCreateView(APIView):
    def get_permissions(self):
        return [IsAuthenticated()] if self.request.method == "POST" else []

    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        reviews = ProductReview.objects.filter(product=product).select_related("customer")
        summary = reviews.aggregate(average_rating=Avg("rating"), review_count=Count("id"))
        return Response({"average_rating": round(summary["average_rating"] or 0, 2), "review_count": summary["review_count"], "reviews": ProductReviewSerializer(reviews, many=True).data})

    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        if ProductReview.objects.filter(product=product, customer=request.user).exists():
            return Response({"detail": "You have already reviewed this product."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ProductReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save(product=product, customer=request.user)
        return Response(ProductReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ProductReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, review_id):
        return get_object_or_404(ProductReview, pk=review_id, customer=request.user)

    def patch(self, request, review_id):
        serializer = ProductReviewSerializer(self.get_object(request, review_id), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(ProductReviewSerializer(serializer.save()).data)

    def delete(self, request, review_id):
        self.get_object(request, review_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
