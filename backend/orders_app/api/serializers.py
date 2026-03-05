from rest_framework import serializers
from rest_framework.exceptions import NotFound

from core.serializer_fields import UTCDateTimeField
from offers_app.models import OfferDetail
from orders_app.models import Order


class OrderCreateSerializer(serializers.Serializer):
    """POST body: offer_detail_id. Creates order from OfferDetail."""

    offer_detail_id = serializers.IntegerField(min_value=1)

    def create(self, validated_data):
        detail = OfferDetail.objects.filter(
            pk=validated_data['offer_detail_id'],
        ).select_related('offer').first()
        if not detail:
            raise NotFound('Das angegebene Angebotsdetail wurde nicht gefunden.')
        request = self.context['request']
        order = Order.objects.create(
            customer_user=request.user,
            business_user=detail.offer.user,
            title=detail.title,
            revisions=detail.revisions,
            delivery_time=detail.delivery_time,
            price=detail.price,
            features=detail.features or [],
            offer_type=detail.offer_type or '',
            status='in_progress',
        )
        return order


PATCH_ALLOWED_STATUSES = ['in_progress', 'completed', 'cancelled']


class OrderStatusUpdateSerializer(serializers.Serializer):
    """PATCH body: only status. Allowed: in_progress, completed, cancelled."""

    status = serializers.ChoiceField(choices=PATCH_ALLOWED_STATUSES)

    def update(self, instance, validated_data):
        instance.status = validated_data['status']
        instance.save(update_fields=['status', 'updated_at'])
        return instance


class OrderListSerializer(serializers.ModelSerializer):
    """List view: id, customer_user, business_user, title, revisions, delivery_time_in_days, price, features, offer_type, status, created_at, updated_at."""

    delivery_time_in_days = serializers.IntegerField(source='delivery_time')
    price = serializers.IntegerField()
    created_at = UTCDateTimeField(read_only=True)
    updated_at = UTCDateTimeField(read_only=True)

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
