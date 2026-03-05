from rest_framework import serializers

from reviews_app.models import Review


class ReviewListSerializer(serializers.ModelSerializer):
    """List view: id, business_user, reviewer, rating, description, created_at, updated_at."""

    class Meta:
        model = Review
        fields = [
            'id',
            'business_user',
            'reviewer',
            'rating',
            'description',
            'created_at',
            'updated_at',
        ]
