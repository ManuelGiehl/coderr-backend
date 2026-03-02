from rest_framework import serializers

from profiles_app.models import Profile


def _empty_str(value):
    return value if value is not None and value != '' else ''


class ProfileSerializer(serializers.ModelSerializer):
    """CRUD serializer for profile. Explicit fields; no null for spec fields."""

    user = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(
        source='user.email', required=False, allow_blank=True
    )
    first_name = serializers.CharField(
        source='user.first_name', required=False, allow_blank=True
    )
    last_name = serializers.CharField(
        source='user.last_name', required=False, allow_blank=True
    )
    type = serializers.CharField(
        source='user.user_profile.user_type', read_only=True
    )

    class Meta:
        model = Profile
        fields = [
            'user',
            'username',
            'first_name',
            'last_name',
            'file',
            'location',
            'tel',
            'description',
            'working_hours',
            'type',
            'email',
            'created_at',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for key in (
            'first_name', 'last_name', 'location', 'tel',
            'description', 'working_hours',
        ):
            data[key] = _empty_str(data.get(key))
        return data

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.user.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
