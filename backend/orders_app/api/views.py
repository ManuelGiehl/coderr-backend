from django.db.models import Q
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from orders_app.api.serializers import OrderListSerializer
from orders_app.models import Order


class OrderListView(ListAPIView):
    """
    GET /api/orders/: list orders where the authenticated user is
    either customer or business partner. Auth required.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = OrderListSerializer

    def get_queryset(self):
        return Order.objects.filter(
            Q(customer_user=self.request.user)
            | Q(business_user=self.request.user),
        ).order_by('-created_at')
