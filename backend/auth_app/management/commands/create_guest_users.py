"""
Management command to create guest users for frontend demo login.

Creates users matching frontend/shared/scripts/config.js GUEST_LOGINS:
- customer: username andrey, password asdasd
- business: username kevin, password asdasd24
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token

from auth_app.models import UserProfile
from profiles_app.models import Profile


GUEST_USERS = [
    {
        'username': 'andrey',
        'password': 'asdasd',
        'user_type': UserProfile.UserType.CUSTOMER,
        'email': 'andrey@example.com',
    },
    {
        'username': 'kevin',
        'password': 'asdasd24',
        'user_type': UserProfile.UserType.BUSINESS,
        'email': 'kevin@example.com',
    },
]


class Command(BaseCommand):
    help = 'Create guest users (andrey/customer, kevin/business) for demo login.'

    def handle(self, *args, **options):
        for data in GUEST_USERS:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'is_active': True,
                },
            )
            if created:
                user.set_password(data['password'])
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f"User '{user.username}' created.")
                )
            else:
                user.set_password(data['password'])
                user.save()
                self.stdout.write(
                    f"User '{user.username}' already exists; password updated."
                )

            UserProfile.objects.get_or_create(
                user=user,
                defaults={'user_type': data['user_type']},
            )
            Profile.objects.get_or_create(user=user, defaults={})
            Token.objects.get_or_create(user=user)

        self.stdout.write(
            self.style.SUCCESS('Guest users ready. Login: andrey/asdasd (Kunde), kevin/asdasd24 (Anbieter).')
        )
