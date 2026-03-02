from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

# Use ModelViewSet for CRUD, APIView for single endpoints.
# Set queryset, serializer_class; use get_queryset() for dynamic data.
# Declare permission_classes.
