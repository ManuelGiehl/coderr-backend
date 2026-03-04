from django.db.models import Min
from rest_framework import serializers

from offers_app.models import Offer, OfferDetail


class OfferDetailCreateSerializer(serializers.Serializer):
    """Nested serializer for one detail when creating an offer."""

    title = serializers.CharField(max_length=255)
    revisions = serializers.IntegerField(min_value=0)
    delivery_time_in_days = serializers.IntegerField(min_value=1)
    price = serializers.IntegerField(min_value=0)
    features = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
    )
    offer_type = serializers.CharField(max_length=50)


class OfferCreateSerializer(serializers.Serializer):
    """Validates and creates offer with exactly 3 details."""

    title = serializers.CharField(max_length=255)
    image = serializers.CharField(
        required=False, allow_blank=True, allow_null=True,
    )
    description = serializers.CharField(required=False, allow_blank=True)
    details = serializers.ListField(
        child=OfferDetailCreateSerializer(),
        min_length=3,
        max_length=3,
    )

    def create(self, validated_data):
        user = self.context['request'].user
        details_data = validated_data.pop('details')
        image = validated_data.get('image')
        offer = Offer.objects.create(
            user=user,
            title=validated_data['title'],
            image=(image or '') if image is not None else '',
            description=validated_data.get('description', ''),
        )
        for d in details_data:
            OfferDetail.objects.create(
                offer=offer,
                title=d['title'],
                revisions=d['revisions'],
                delivery_time=d['delivery_time_in_days'],
                price=d['price'],
                features=d.get('features', []),
                offer_type=d.get('offer_type', ''),
            )
        return offer


class OfferDetailResponseSerializer(serializers.ModelSerializer):
    """Full detail for 201 response; price as integer per spec."""

    delivery_time_in_days = serializers.IntegerField(source='delivery_time')
    price = serializers.IntegerField()

    class Meta:
        model = OfferDetail
        fields = [
            'id',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
        ]


class OfferCreateResponseSerializer(serializers.ModelSerializer):
    """Offer with full details for 201 response."""

    details = OfferDetailResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id',
            'title',
            'image',
            'description',
            'details',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('image') == '':
            data['image'] = None
        return data


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
