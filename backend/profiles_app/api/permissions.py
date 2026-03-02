from rest_framework import permissions


class IsProfileOwner(permissions.BasePermission):
    """Allow PATCH only for the profile owner; GET remains for any authenticated user."""

    def has_object_permission(self, request, view, obj):
        if request.method in ('PATCH', 'PUT'):
            return request.user == obj.user
        return True
