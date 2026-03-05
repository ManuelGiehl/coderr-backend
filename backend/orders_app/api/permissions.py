from rest_framework import permissions


class IsCustomerUser(permissions.BasePermission):
    """Only users with user_type 'customer' can create orders."""

    message = 'Only customer users can create orders.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'user_profile'):
            return False
        return request.user.user_profile.user_type == 'customer'


class IsBusinessUser(permissions.BasePermission):
    """Only users with user_type 'business' can update order status."""

    message = 'Only business users can update order status.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'user_profile'):
            return False
        return request.user.user_profile.user_type == 'business'


class IsOrderBusinessUser(permissions.BasePermission):
    """Only the business_user of the order can update it (PATCH)."""

    message = 'You do not have permission to update this order.'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return obj.business_user_id == request.user.id
