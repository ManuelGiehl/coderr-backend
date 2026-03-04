from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from profiles_app.models import Profile


class CustomerProfileListEndpointTest(TestCase):
    """
    GET /api/profiles/customer/ per spec:
    200 = list of customer profiles, 401 = not authenticated.
    Happy and unhappy path tests; response fields must not be null.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/profiles/customer/'
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
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Token {self.token.key}'}

    # --- Happy path: 200 ---

    def test_get_customer_profiles_authenticated_returns_200(self):
        response = self.client.get(self.url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_customer_profiles_returns_list(self):
        response = self.client.get(self.url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)

    def test_get_customer_profiles_includes_only_customer_users(self):
        customer_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@test.de',
            password='password1234',
        )
        UserProfile.objects.create(user=customer_user, user_type='customer')
        Profile.objects.get_or_create(user=customer_user, defaults={})
        response = self.client.get(self.url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['username'], 'otheruser')
        self.assertEqual(data[0]['type'], 'customer')

    def test_get_customer_profiles_response_fields_no_null(self):
        customer_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@test.de',
            password='password1234',
        )
        UserProfile.objects.create(user=customer_user, user_type='customer')
        Profile.objects.get_or_create(user=customer_user, defaults={})
        response = self.client.get(self.url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertGreater(len(data), 0)
        item = data[0]
        for key in (
            'first_name', 'last_name', 'location', 'tel',
            'description', 'working_hours',
        ):
            self.assertIn(key, item)
            self.assertIsNotNone(item[key])
            self.assertIsInstance(item[key], str)

    # --- Unhappy path: 401 ---

    def test_get_customer_profiles_without_auth_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_customer_profiles_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
