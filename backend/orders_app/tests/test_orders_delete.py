from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from orders_app.models import Order


class OrderDeleteEndpointTest(TestCase):
    """
    DELETE /api/orders/{id}/ per spec:
    204 = order deleted (admin/staff only), 401 = not authenticated,
    403 = not staff, 404 = order not found.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.de',
            password='password1234',
            is_staff=True,
        )
        UserProfile.objects.create(user=self.admin_user, user_type='business')
        self.admin_token = Token.objects.create(user=self.admin_user)
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@test.de',
            password='password1234',
        )
        UserProfile.objects.create(user=self.customer, user_type='customer')
        self.customer_token = Token.objects.create(user=self.customer)
        self.business = User.objects.create_user(
            username='business',
            email='business@test.de',
            password='password1234',
        )
        UserProfile.objects.create(user=self.business, user_type='business')
        self.business_token = Token.objects.create(user=self.business)
        self.order = Order.objects.create(
            customer_user=self.customer,
            business_user=self.business,
            title='Logo Design',
            revisions=3,
            delivery_time=5,
            price=Decimal('150'),
            features=['Logo Design', 'Visitenkarten'],
            offer_type='basic',
            status='in_progress',
        )
        self.url = f'/api/orders/{self.order.id}/'

    # --- Happy path: 204 ---

    def test_delete_order_admin_returns_204(self):
        response = self.client.delete(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.admin_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_order_response_has_no_content(self):
        response = self.client.delete(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.admin_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

    def test_delete_order_removes_from_db(self):
        order_id = self.order.id
        self.client.delete(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.admin_token.key}',
        )
        self.assertFalse(Order.objects.filter(pk=order_id).exists())

    # --- Unhappy path: 401 ---

    def test_delete_order_without_auth_returns_401(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_order_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Unhappy path: 403 ---

    def test_delete_order_customer_returns_403(self):
        response = self.client.delete(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_order_business_non_staff_returns_403(self):
        response = self.client.delete(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Unhappy path: 404 ---

    def test_delete_order_not_found_returns_404(self):
        url = '/api/orders/99999/'
        response = self.client.delete(
            url,
            HTTP_AUTHORIZATION=f'Token {self.admin_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
