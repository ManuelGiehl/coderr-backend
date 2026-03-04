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


class IsOfferOwner(permissions.BasePermission):
    """Only the creator of the offer can modify it (PATCH). GET allowed for any authenticated user."""

    message = 'Only the creator of the offer can modify it.'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return obj.user_id == request.user.id
