from rest_framework import serializers

from core.serializer_fields import UTCDateTimeField
from reviews_app.models import Review


class ReviewCreateSerializer(serializers.Serializer):
    """POST body: business_user (id), rating (1-5), description. One review per business user per customer."""

    business_user = serializers.IntegerField(min_value=1)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    description = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_business_user(self, value):
        from django.contrib.auth import get_user_model
        if not get_user_model().objects.filter(pk=value).exists():
            raise serializers.ValidationError('Business user not found.')
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return attrs
        if Review.objects.filter(
            reviewer=request.user,
            business_user_id=attrs['business_user'],
        ).exists():
            raise serializers.ValidationError(
                {'business_user': 'You can only submit one review per business profile.'},
            )
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        return Review.objects.create(
            business_user_id=validated_data['business_user'],
            reviewer=request.user,
            rating=validated_data['rating'],
            description=validated_data.get('description', ''),
        )


class ReviewUpdateSerializer(serializers.Serializer):
    """PATCH body: only rating (1-5) and/or description are editable."""

    rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    description = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        if 'rating' in validated_data:
            instance.rating = validated_data['rating']
        if 'description' in validated_data:
            instance.description = validated_data['description']
        instance.save(update_fields=['rating', 'description', 'updated_at'])
        return instance


class ReviewListSerializer(serializers.ModelSerializer):
    """List view: id, business_user, reviewer, rating, description, created_at, updated_at."""

    created_at = UTCDateTimeField(read_only=True)
    updated_at = UTCDateTimeField(read_only=True)

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
