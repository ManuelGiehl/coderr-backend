from django.db.models import Min
from rest_framework import serializers

from offers_app.models import Offer


class OfferListSerializer(serializers.ModelSerializer):
    """List view: explicit fields; details as id+url; min_price, min_delivery_time, user_details."""

    details = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id',
            'user',
            'title',
            'image',
            'description',
            'created_at',
            'updated_at',
            'details',
            'min_price',
            'min_delivery_time',
            'user_details',
        ]

    def get_details(self, obj):
        return [
            {'id': d.id, 'url': f'/offerdetails/{d.id}/'}
            for d in obj.details.all().order_by('id')
        ]

    def get_min_price(self, obj):
        result = obj.details.aggregate(min_p=Min('price'))
        val = result.get('min_p')
        return float(val) if val is not None else None

    def get_min_delivery_time(self, obj):
        result = obj.details.aggregate(min_d=Min('delivery_time'))
        return result.get('min_d')

    def get_user_details(self, obj):
        u = obj.user
        return {
            'first_name': u.first_name or '',
            'last_name': u.last_name or '',
            'username': u.username,
        }
