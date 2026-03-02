from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from profiles_app.api.permissions import IsProfileOwner
from profiles_app.api.serializers import ProfileSerializer
from profiles_app.models import Profile


class ProfileDetailView(APIView):
    """GET and PATCH /api/profile/<pk>/; auth required; PATCH only for owner."""

    permission_classes = [IsAuthenticated, IsProfileOwner]

    def get_object(self, pk):
        profile = get_object_or_404(Profile, user_id=pk)
        return profile

    def get(self, request, pk):
        profile = self.get_object(pk)
        self.check_object_permissions(request, profile)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        profile = self.get_object(pk)
        self.check_object_permissions(request, profile)
        serializer = ProfileSerializer(
            profile, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
