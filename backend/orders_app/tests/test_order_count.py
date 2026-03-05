from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from orders_app.models import Order


class OrderCountEndpointTest(TestCase):
    """
    GET /api/order-count/{business_user_id}/ per spec:
    200 = order count for business user (in_progress only), 401 = not authenticated,
    404 = no business user with that ID.
    """

    def setUp(self):
        self.client = APIClient()
        self.business = User.objects.create_user(
            username='business',
            email='business@test.de',
            password='password1234',
        )
        UserProfile.objects.create(user=self.business, user_type='business')
        self.business_token = Token.objects.create(user=self.business)
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@test.de',
            password='password1234',
        )
        UserProfile.objects.create(user=self.customer, user_type='customer')
        self.customer_token = Token.objects.create(user=self.customer)
        self.other_user = User.objects.create_user(
            username='other',
            email='other@test.de',
            password='password1234',
        )
        # no UserProfile – not a business user
        self.other_token = Token.objects.create(user=self.other_user)

    def _url(self, business_user_id):
        return f'/api/order-count/{business_user_id}/'

    # --- Happy path: 200 ---

    def test_get_order_count_returns_200(self):
        response = self.client.get(
            self._url(self.business.id),
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_order_count_response_structure(self):
        response = self.client.get(
            self._url(self.business.id),
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('order_count', data)
        self.assertIsInstance(data['order_count'], int)
        self.assertEqual(data['order_count'], 0)

    def test_get_order_count_in_progress_only(self):
        Order.objects.create(
            customer_user=self.customer,
            business_user=self.business,
            title='Order 1',
            revisions=0,
            delivery_time=5,
            price=Decimal('100'),
            features=[],
            offer_type='basic',
            status='in_progress',
        )
        Order.objects.create(
            customer_user=self.customer,
            business_user=self.business,
            title='Order 2',
            revisions=0,
            delivery_time=5,
            price=Decimal('200'),
            features=[],
            offer_type='basic',
            status='completed',
        )
        response = self.client.get(
            self._url(self.business.id),
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['order_count'], 1)

    def test_get_order_count_any_authenticated_user(self):
        response = self.client.get(
            self._url(self.business.id),
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['order_count'], 0)

    # --- Unhappy path: 401 ---

    def test_get_order_count_without_auth_returns_401(self):
        response = self.client.get(self._url(self.business.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_order_count_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid')
        response = self.client.get(self._url(self.business.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Unhappy path: 404 ---

    def test_get_order_count_nonexistent_user_returns_404(self):
        response = self.client.get(
            self._url(99999),
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_order_count_customer_user_id_returns_404(self):
        response = self.client.get(
            self._url(self.customer.id),
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_order_count_user_without_profile_returns_404(self):
        response = self.client.get(
            self._url(self.other_user.id),
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
