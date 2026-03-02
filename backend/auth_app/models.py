from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """Stores user type (customer/business). Data structure only."""

    class UserType(models.TextChoices):
        CUSTOMER = 'customer', 'Customer'
        BUSINESS = 'business', 'Business'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_profile',
    )
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
    )

    class Meta:
        verbose_name = 'User profile'
        verbose_name_plural = 'User profiles'
        ordering = ['user_id']

    def __str__(self):
        return f"{self.user.username} ({self.get_user_type_display()})"
