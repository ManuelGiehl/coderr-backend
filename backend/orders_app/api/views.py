from django.db.models import Q
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders_app.api.permissions import IsCustomerUser
from orders_app.api.serializers import OrderCreateSerializer, OrderListSerializer
from orders_app.models import Order


class OrderListView(ListCreateAPIView):
    """
    GET /api/orders/: list orders where user is customer or business. Auth required.
    POST /api/orders/: create order from OfferDetail (offer_detail_id). Customer only.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = OrderListSerializer

    def get_queryset(self):
        return Order.objects.filter(
            Q(customer_user=self.request.user)
            | Q(business_user=self.request.user),
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsCustomerUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        response_serializer = OrderListSerializer(order)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )
