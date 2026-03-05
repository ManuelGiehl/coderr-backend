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


class IsReviewAuthor(permissions.BasePermission):
    """Only the creator (reviewer) of the review can update it (PATCH)."""

    message = 'You are not authorized to edit this review.'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return obj.reviewer_id == request.user.id
