from django.db.models import Min, Q
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from offers_app.api.permissions import IsBusinessUser
from offers_app.api.serializers import (
    OfferCreateResponseSerializer,
    OfferCreateSerializer,
    OfferListSerializer,
)
from offers_app.models import Offer


class OfferPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class OfferListView(ListCreateAPIView):
    """
    GET /api/offers/: paginated list; no auth.
    POST /api/offers/: create offer (3 details); business user only.
    """

    serializer_class = OfferListSerializer
    pagination_class = OfferPageNumberPagination

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsBusinessUser()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OfferCreateSerializer
        return OfferListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        offer = serializer.save()
        response_serializer = OfferCreateResponseSerializer(offer)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def get_queryset(self):
        params = self.request.query_params
        qs = (
            Offer.objects
            .select_related('user')
            .prefetch_related('details')
            .annotate(
                min_p=Min('details__price'),
                min_delivery=Min('details__delivery_time'),
            )
        )
        creator_id = params.get('creator_id')
        if creator_id is not None:
            try:
                qs = qs.filter(user_id=int(creator_id))
            except ValueError:
                raise ValidationError({'creator_id': 'Must be an integer.'})
        min_price = params.get('min_price')
        if min_price is not None:
            try:
                qs = qs.filter(min_p__gte=float(min_price))
            except ValueError:
                raise ValidationError({'min_price': 'Must be a number.'})
        max_delivery_time = params.get('max_delivery_time')
        if max_delivery_time is not None:
            try:
                qs = qs.filter(min_delivery__lte=int(max_delivery_time))
            except ValueError:
                raise ValidationError(
                    {'max_delivery_time': 'Must be an integer.'},
                )
        search = params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search),
            )
        ordering = params.get('ordering', 'updated_at')
        if ordering not in (
            'updated_at', 'min_price', '-updated_at', '-min_price',
        ):
            raise ValidationError(
                {'ordering': "Must be 'updated_at' or 'min_price'."},
            )
        if ordering == 'min_price':
            qs = qs.order_by('min_p')
        elif ordering == '-min_price':
            qs = qs.order_by('-min_p')
        else:
            qs = qs.order_by(ordering)
        return qs
