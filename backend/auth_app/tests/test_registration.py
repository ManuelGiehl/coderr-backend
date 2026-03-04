from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from auth_app.models import UserProfile


class RegistrationEndpointTest(TestCase):
    """Tests for POST /api/registration/ status codes and response shape."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/registration/'
        self.valid_payload = {
            'username': 'test',
            'email': 'test@test.de',
            'password': 'password1234',
            'repeated_password': 'password1234',
            'type': 'customer',
        }

    def test_registration_success_returns_201(self):
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_registration_success_returns_token_and_user_info(self):
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('token', data)
        self.assertIn('username', data)
        self.assertIn('email', data)
        self.assertIn('user_id', data)
        self.assertEqual(data['username'], self.valid_payload['username'])
        self.assertEqual(data['email'], self.valid_payload['email'])
        self.assertEqual(data['user_id'], User.objects.get(username='test').id)

    def test_registration_success_creates_user_and_profile(self):
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='test').exists())
        user = User.objects.get(username='test')
        self.assertTrue(
            UserProfile.objects.filter(user=user, user_type='customer').exists()
        )

    def test_registration_missing_fields_returns_400(self):
        response = self.client.post(
            self.url,
            {'username': 'test'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_password_mismatch_returns_400(self):
        payload = {**self.valid_payload, 'repeated_password': 'different'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('repeated_password', response.json())

    def test_registration_invalid_type_returns_400(self):
        payload = {**self.valid_payload, 'type': 'invalid'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_username_returns_400(self):
        self.client.post(self.url, self.valid_payload, format='json')
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.json())

    def test_registration_duplicate_email_returns_400(self):
        self.client.post(self.url, self.valid_payload, format='json')
        payload = {
            **self.valid_payload,
            'username': 'otheruser',
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.json())

    def test_registration_invalid_email_returns_400(self):
        payload = {**self.valid_payload, 'email': 'not-an-email'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
