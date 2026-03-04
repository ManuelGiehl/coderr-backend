from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class LoginEndpointTest(TestCase):
    """
    POST /api/login/ status codes per spec:
    200 = successful login, 400 = invalid request data, 500 = server error.
    Tests cover happy path (200) and unhappy paths (400 only; no 500 for bad input).
    """

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/login/'
        User.objects.create_user(
            username='test',
            email='test@test.de',
            password='password1234',
        )
        self.valid_payload = {
            'username': 'test',
            'password': 'password1234',
        }

    # --- Happy path: 200 + correct response ---

    def test_login_success_returns_200(self):
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_success_returns_token_and_user_info(self):
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('token', data)
        self.assertIn('username', data)
        self.assertIn('email', data)
        self.assertIn('user_id', data)
        self.assertEqual(data['username'], self.valid_payload['username'])
        self.assertEqual(data['email'], 'test@test.de')
        self.assertEqual(data['user_id'], User.objects.get(username='test').id)

    def test_login_success_token_is_non_empty(self):
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json().get('token'))

    # --- Unhappy path: 400 invalid request data (never 500 for bad input) ---

    def test_login_missing_username_returns_400(self):
        response = self.client.post(
            self.url,
            {'password': 'password1234'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.json())

    def test_login_missing_password_returns_400(self):
        response = self.client.post(
            self.url,
            {'username': 'test'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.json())

    def test_login_missing_both_fields_returns_400(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_wrong_password_returns_400(self):
        payload = {**self.valid_payload, 'password': 'wrong'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_unknown_username_returns_400(self):
        payload = {
            'username': 'otheruser',
            'password': 'password1234',
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_empty_username_returns_400(self):
        payload = {**self.valid_payload, 'username': ''}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_empty_password_returns_400(self):
        payload = {**self.valid_payload, 'password': ''}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_invalid_credentials_return_400_not_500(self):
        payload = {'username': 'otheruser', 'password': 'wrong'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
