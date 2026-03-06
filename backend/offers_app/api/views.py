from django.db.models import Min, Prefetch
from rest_framework import status
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from offers_app.api.filters import apply_offer_list_filters
from offers_app.api.permissions import IsBusinessUser, IsOfferOwner
from offers_app.api.serializers import (
    OfferCreateResponseSerializer,
    OfferCreateSerializer,
    OfferDetailResponseSerializer,
    OfferListSerializer,
    OfferUpdateSerializer,
)
from offers_app.models import Offer, OfferDetail


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
        base_qs = (
            Offer.objects
            .select_related('user')
            .prefetch_related('details')
            .annotate(
                min_p=Min('details__price'),
                min_delivery=Min('details__delivery_time'),
            )
        )
        return apply_offer_list_filters(base_qs, self.request.query_params)


class OfferDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET /api/offers/<id>/: single offer; auth required.
    PATCH /api/offers/<id>/: partial update; only offer creator; returns full offer.
    DELETE /api/offers/<id>/: delete offer; only offer creator; 204 No Content.
    """

    permission_classes = [IsAuthenticated, IsOfferOwner]
    serializer_class = OfferListSerializer

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return OfferUpdateSerializer
        return OfferListSerializer

    def get_queryset(self):
        return (
            Offer.objects
            .select_related('user')
            .prefetch_related('details')
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance = (
            Offer.objects.filter(pk=instance.pk)
            .prefetch_related(
                Prefetch('details', queryset=OfferDetail.objects.order_by('id')),
            )
            .first()
        )
        response_serializer = OfferCreateResponseSerializer(
            instance,
            context={'request': request},
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class OfferDetailRetrieveView(RetrieveAPIView):
    """
    GET /api/offerdetails/<id>/: single offer detail; auth required.
    Returns id, title, revisions, delivery_time_in_days, price, features, offer_type.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = OfferDetailResponseSerializer
    queryset = OfferDetail.objects.all()
