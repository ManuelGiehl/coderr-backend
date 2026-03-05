from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from reviews_app.api.permissions import IsCustomerUser, IsReviewAuthor
from reviews_app.api.serializers import (
    ReviewCreateSerializer,
    ReviewListSerializer,
    ReviewUpdateSerializer,
)
from reviews_app.models import Review


class ReviewListView(ListCreateAPIView):
    """
    GET /api/reviews/: list all reviews. Authenticated users only.
    POST /api/reviews/: create review. Customer users only; one per business user.
    Query params (GET): business_user_id, reviewer_id, ordering.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ReviewListSerializer

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReviewCreateSerializer
        return ReviewListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsCustomerUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        response_serializer = ReviewListSerializer(review)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def get_queryset(self):
        qs = Review.objects.all()
        business_user_id = self.request.query_params.get('business_user_id')
        if business_user_id is not None:
            try:
                qs = qs.filter(business_user_id=int(business_user_id))
            except ValueError:
                pass
        reviewer_id = self.request.query_params.get('reviewer_id')
        if reviewer_id is not None:
            try:
                qs = qs.filter(reviewer_id=int(reviewer_id))
            except ValueError:
                pass
        ordering = self.request.query_params.get('ordering', '').strip()
        if ordering in ('updated_at', '-updated_at', 'rating', '-rating'):
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by('-updated_at')
        return qs


class ReviewDetailView(RetrieveUpdateAPIView):
    """
    GET /api/reviews/{id}/: retrieve a review. Authenticated users only.
    PATCH /api/reviews/{id}/: update rating and/or description. Only the creator (reviewer).
    """

    permission_classes = [IsAuthenticated, IsReviewAuthor]
    serializer_class = ReviewListSerializer
    queryset = Review.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return ReviewUpdateSerializer
        return ReviewListSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_serializer = ReviewListSerializer(instance)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )
