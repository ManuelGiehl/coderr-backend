from rest_framework import permissions


class IsCustomerUser(permissions.BasePermission):
    """Only users with user_type 'customer' can create reviews."""

    message = 'Only customer users can create reviews.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'user_profile'):
            return False
        return request.user.user_profile.user_type == 'customer'
