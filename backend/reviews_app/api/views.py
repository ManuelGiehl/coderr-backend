from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from reviews_app.api.serializers import ReviewListSerializer
from reviews_app.models import Review


class ReviewListView(ListAPIView):
    """
    GET /api/reviews/: list all reviews. Authenticated users only.
    Query params: business_user_id, reviewer_id (filter), ordering (updated_at or rating).
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ReviewListSerializer

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
