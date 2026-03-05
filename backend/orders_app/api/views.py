from django.db.models import Q
from rest_framework import status
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from orders_app.api.permissions import (
    IsBusinessUser,
    IsCustomerUser,
    IsOrderBusinessUser,
)
from orders_app.api.serializers import (
    OrderCreateSerializer,
    OrderListSerializer,
    OrderStatusUpdateSerializer,
)
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


class OrderDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET /api/orders/{id}/: retrieve order (customer or business of that order).
    PATCH /api/orders/{id}/: update order status. Business user (order owner) only.
    DELETE /api/orders/{id}/: delete order. Admin (staff) only. Returns 204 No Content.
    """

    permission_classes = [IsAuthenticated, IsOrderBusinessUser]
    serializer_class = OrderListSerializer

    def get_queryset(self):
        if self.request.method in ('PATCH', 'DELETE'):
            return Order.objects.all()
        return Order.objects.filter(
            Q(customer_user=self.request.user)
            | Q(business_user=self.request.user),
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return OrderStatusUpdateSerializer
        return OrderListSerializer

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsAdminUser()]
        if self.request.method == 'PATCH':
            return [
                IsAuthenticated(),
                IsBusinessUser(),
                IsOrderBusinessUser(),
            ]
        return [IsAuthenticated(), IsOrderBusinessUser()]

    def perform_update(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = OrderListSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
