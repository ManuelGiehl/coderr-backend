import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Min
from rest_framework import serializers

from core.serializer_fields import UTCDateTimeField
from offers_app.models import Offer, OfferDetail


class ImageUploadOrPathField(serializers.Field):
    """Accepts either an uploaded file (multipart) or a path string (JSON)."""

    def to_internal_value(self, data):
        if hasattr(data, 'read') and hasattr(data, 'name'):
            return data
        if isinstance(data, str):
            return data
        raise serializers.ValidationError('Expected image file or path string.')


class OfferDetailCreateSerializer(serializers.Serializer):
    """Nested serializer for one detail when creating an offer."""

    title = serializers.CharField(max_length=255)
    revisions = serializers.IntegerField(required=False, allow_null=True, min_value=-1)
    delivery_time_in_days = serializers.IntegerField(
        required=False, allow_null=True, min_value=1, default=1,
    )
    price = serializers.IntegerField(
        required=False, allow_null=True, min_value=0, default=0,
    )
    features = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
    )
    offer_type = serializers.CharField(max_length=50, allow_blank=False)

    def validate_offer_type(self, value):
        """Per API spec: offer_type must be sent to uniquely identify the detail (required for PATCH)."""
        if not value or not str(value).strip():
            raise serializers.ValidationError(
                'offer_type is required to identify the detail.',
            )
        return value.strip()

    def validate_revisions(self, value):
        """Frontend sends -1 for 'limitless'; store as 0."""
        if value is None or value < 0:
            return 0
        return value

    def validate_delivery_time_in_days(self, value):
        if value is None:
            return 1
        return value

    def validate_price(self, value):
        if value is None:
            return 0
        return value


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
        if instance.image:
            request = self.context.get('request')
            if request:
                data['image'] = request.build_absolute_uri(
                    settings.MEDIA_URL + instance.image
                )
            else:
                data['image'] = settings.MEDIA_URL + instance.image
        else:
            data['image'] = None
        return data


class OfferUpdateSerializer(serializers.Serializer):
    """Partial update: only provided fields are updated. Details can be 1–3; each identified by offer_type."""

    title = serializers.CharField(max_length=255, required=False)
    image = ImageUploadOrPathField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    details = serializers.ListField(
        child=OfferDetailCreateSerializer(),
        min_length=1,
        max_length=3,
        required=False,
    )

    def to_internal_value(self, data):
        """Treat empty details list as omitted so PATCH with only title/details:[] succeeds."""
        if isinstance(data, dict) and 'details' in data and data['details'] == []:
            data = {k: v for k, v in data.items() if k != 'details'}
        return super().to_internal_value(data)

    def _save_uploaded_image(self, instance, uploaded_file):
        """Save uploaded file to media/offers/ and return relative path."""
        name = getattr(uploaded_file, 'name', 'image')
        ext = os.path.splitext(name)[1] or '.jpg'
        safe_name = f'offer_{instance.pk}_{uuid.uuid4().hex[:8]}{ext}'
        path = os.path.join('offers', safe_name)
        saved_path = default_storage.save(path, uploaded_file)
        return saved_path

    def update(self, instance, validated_data):
        if 'title' in validated_data:
            instance.title = validated_data['title']
        if 'image' in validated_data:
            value = validated_data['image']
            if value is None:
                instance.image = instance.image
            elif hasattr(value, 'read'):
                instance.image = self._save_uploaded_image(instance, value)
            else:
                instance.image = (value or '') if isinstance(value, str) else instance.image
        if 'description' in validated_data:
            instance.description = validated_data.get('description', '')
        if 'details' in validated_data:
            details_data = validated_data['details']
            for d in details_data:
                offer_type = d.get('offer_type', '')
                detail_obj = instance.details.filter(offer_type=offer_type).first()
                if detail_obj:
                    detail_obj.title = d['title']
                    detail_obj.revisions = d['revisions']
                    detail_obj.delivery_time = d['delivery_time_in_days']
                    detail_obj.price = d['price']
                    detail_obj.features = d.get('features', [])
                    detail_obj.offer_type = offer_type
                    detail_obj.save()
        instance.save()
        return instance


class OfferListSerializer(serializers.ModelSerializer):
    """List view: explicit fields; details as id+url; min_price, min_delivery_time, user_details."""

    details = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    created_at = UTCDateTimeField(read_only=True)
    updated_at = UTCDateTimeField(read_only=True)

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

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(settings.MEDIA_URL + obj.image)
        return settings.MEDIA_URL + obj.image

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
