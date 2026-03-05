"""
Shared serializer fields for the API.
UTCDateTimeField serializes datetime values as ISO 8601 with Z (UTC) for test compatibility.
"""

from datetime import timezone

from django.utils import timezone as dj_timezone
from rest_framework import serializers


class UTCDateTimeField(serializers.DateTimeField):
    """
    DateTimeField that always serializes to UTC with 'Z' suffix.
    Matches format: YYYY-MM-DDTHH:MM:SS[.microseconds]Z
    """

    def to_representation(self, value):
        if value is None:
            return None
        if value.tzinfo is None:
            value = dj_timezone.make_aware(value)
        value_utc = value.astimezone(timezone.utc)
        iso = value_utc.isoformat(timespec='microseconds')
        return iso.replace('+00:00', 'Z')
