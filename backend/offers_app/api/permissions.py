from rest_framework import permissions


class IsBusinessUser(permissions.BasePermission):
    """Only users with user_type 'business' can create/edit offers."""

    message = 'Only business users can create offers.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'user_profile'):
            return False
        return request.user.user_profile.user_type == 'business'
