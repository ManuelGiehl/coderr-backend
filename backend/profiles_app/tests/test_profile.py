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
    200 = success, 401 = not authenticated, 403 = not profile owner (PATCH only),
    404 = profile not found. Happy and unhappy path tests for status codes.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='test',
            first_name='test',
            last_name='test',
            email='test@test.de',
            password='password1234',
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

    def test_patch_profile_returns_updated_data_no_null(self):
        payload = {
            'first_name': 'Max',
            'last_name': 'Mustermann',
            'location': 'Berlin',
            'tel': '987654321',
            'description': 'Updated business description',
            'working_hours': '10-18',
            'email': 'new_email@business.de',
        }
        response = self.client.patch(
            self.url,
            payload,
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['first_name'], payload['first_name'])
        self.assertEqual(data['last_name'], payload['last_name'])
        self.assertEqual(data['location'], payload['location'])
        self.assertEqual(data['tel'], payload['tel'])
        self.assertEqual(data['description'], payload['description'])
        self.assertEqual(data['working_hours'], payload['working_hours'])
        self.assertEqual(data['email'], payload['email'])
        for key in (
            'first_name', 'last_name', 'location', 'tel',
            'description', 'working_hours',
        ):
            self.assertIsNotNone(data[key])
            self.assertIsInstance(data[key], str)

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

    def test_patch_profile_invalid_email_returns_400(self):
        response = self.client.patch(
            self.url,
            {'email': 'not-an-email'},
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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

    # --- Unhappy path: 403 Forbidden (not owner) ---

    def test_patch_profile_other_user_returns_403(self):
        other = User.objects.create_user(
            username='otheruser',
            email='otheruser@test.de',
            password='password1234',
        )
        UserProfile.objects.create(user=other, user_type='customer')
        Profile.objects.get_or_create(user=other, defaults={})
        other_token = Token.objects.create(user=other)
        response = self.client.patch(
            self.url,
            {'first_name': 'Hacked'},
            format='json',
            HTTP_AUTHORIZATION=f'Token {other_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.first_name, 'Hacked')
