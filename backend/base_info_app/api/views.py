from django.db.models import Avg
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import UserProfile
from offers_app.models import Offer
from reviews_app.models import Review


class BaseInfoView(APIView):
    """
    GET /api/base-info/: platform statistics. No authentication required.
    Returns review_count, average_rating (1 decimal), business_profile_count, offer_count.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        review_count = Review.objects.count()
        agg = Review.objects.aggregate(avg=Avg('rating'))
        average_rating = agg['avg']
        if average_rating is None:
            average_rating = 0.0
        else:
            average_rating = round(float(average_rating), 1)
        business_profile_count = UserProfile.objects.filter(
            user_type='business',
        ).count()
        offer_count = Offer.objects.count()
        data = {
            'review_count': review_count,
            'average_rating': average_rating,
            'business_profile_count': business_profile_count,
            'offer_count': offer_count,
        }
        return Response(data)
