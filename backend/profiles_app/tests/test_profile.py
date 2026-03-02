from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from profiles_app.models import Profile


class ProfileEndpointTest(TestCase):
    """
    GET/PATCH /api/profile/{pk}/ per spec:
    200 = success, 401 = not authenticated, 404 = profile not found.
    Happy and unhappy path tests for status codes.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='profileuser',
            email='profile@test.de',
            password='pass1234!',
        )
        UserProfile.objects.create(user=self.user, user_type='business')
        Profile.objects.get_or_create(user=self.user, defaults={})
        self.token = Token.objects.create(user=self.user)
        self.url = f'/api/profile/{self.user.pk}/'
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Token {self.token.key}'}

    # --- Happy path: 200 ---

    def test_get_profile_authenticated_returns_200(self):
        response = self.client.get(
            self.url,
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_profile_returns_required_fields_no_null(self):
        response = self.client.get(
            self.url,
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        for key in (
            'user', 'username', 'first_name', 'last_name',
            'file', 'location', 'tel', 'description',
            'working_hours', 'type', 'email', 'created_at',
        ):
            self.assertIn(key, data)
        for key in ('first_name', 'last_name', 'location', 'tel', 'description', 'working_hours'):
            self.assertIsNotNone(data[key])
            self.assertIsInstance(data[key], str)

    def test_patch_profile_authenticated_returns_200(self):
        response = self.client.patch(
            self.url,
            {'first_name': 'Max', 'location': 'Berlin'},
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- Unhappy path: 401 Unauthorized ---

    def test_get_profile_without_auth_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_profile_without_auth_returns_401(self):
        response = self.client.patch(
            self.url,
            {'first_name': 'Max'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Unhappy path: 404 Not Found ---

    def test_get_profile_nonexistent_pk_returns_404(self):
        response = self.client.get(
            '/api/profile/99999/',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_profile_nonexistent_pk_returns_404(self):
        response = self.client.patch(
            '/api/profile/99999/',
            {'first_name': 'Max'},
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
