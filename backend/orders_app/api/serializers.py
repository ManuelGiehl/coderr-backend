from rest_framework import serializers

from orders_app.models import Order


class OrderListSerializer(serializers.ModelSerializer):
    """List view: id, customer_user, business_user, title, revisions, delivery_time_in_days, price, features, offer_type, status, created_at, updated_at."""

    delivery_time_in_days = serializers.IntegerField(source='delivery_time')
    price = serializers.IntegerField()

    class Meta:
        model = Order
        fields = [
            'id',
            'customer_user',
            'business_user',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
            'status',
            'created_at',
            'updated_at',
        ]
