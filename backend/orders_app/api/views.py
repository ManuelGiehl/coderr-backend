from django.db.models import Q
from rest_framework import status
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import UserProfile
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


class OrderCountView(APIView):
    """
    GET /api/order-count/{business_user_id}/: returns the number of
    ongoing orders (status 'in_progress') for the given business user.
    Authenticated users only. 404 if no business user with that ID.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, business_user_id):
        is_business = UserProfile.objects.filter(
            user_id=business_user_id,
            user_type='business',
        ).exists()
        if not is_business:
            return Response(
                {'detail': 'No business user found with that ID.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        count = Order.objects.filter(
            business_user_id=business_user_id,
            status='in_progress',
        ).count()
        return Response({'order_count': count}, status=status.HTTP_200_OK)


class CompletedOrderCountView(APIView):
    """
    GET /api/completed-order-count/{business_user_id}/: returns the number of
    completed orders (status 'completed') for the given business user.
    Authenticated users only. 404 if no business user with that ID.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, business_user_id):
        is_business = UserProfile.objects.filter(
            user_id=business_user_id,
            user_type='business',
        ).exists()
        if not is_business:
            return Response(
                {'detail': 'No business user found with that ID.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        count = Order.objects.filter(
            business_user_id=business_user_id,
            status='completed',
        ).count()
        return Response(
            {'completed_order_count': count},
            status=status.HTTP_200_OK,
        )
