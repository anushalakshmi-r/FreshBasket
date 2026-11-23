from rest_framework import serializers

from reviews.models import ProductReview


class ProductReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductReview
        fields = ["id", "product", "customer_name", "rating", "title", "body", "created_at", "updated_at"]
        read_only_fields = ["id", "product", "customer_name", "created_at", "updated_at"]

    def get_customer_name(self, obj):
        return obj.customer.get_full_name() or obj.customer.email

    def validate_rating(self, value):
        if value not in range(1, 6):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
