from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from orders_app.models import Order


class OrderListEndpointTest(TestCase):
    """
    GET /api/orders/ per spec:
    200 = list of orders (customer or business), 401 = not authenticated.
    Only orders where user is customer_user or business_user are returned.
    """

    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(
            username='test',
            first_name='test',
            last_name='test',
            email='test@test.de',
            password='password1234',
        )
        self.business = User.objects.create_user(
            username='otheruser',
            email='otheruser@test.de',
            password='password1234',
        )
        self.customer_token = Token.objects.create(user=self.customer)
        self.business_token = Token.objects.create(user=self.business)
        self.third_user = User.objects.create_user(
            username='third',
            email='third@test.de',
            password='password1234',
        )
        self.third_token = Token.objects.create(user=self.third_user)

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
        self.url = '/api/orders/'

    # --- Happy path: 200 ---

    def test_get_orders_as_customer_returns_200(self):
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_orders_returns_list_structure(self):
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        item = data[0]
        self.assertIn('id', item)
        self.assertIn('customer_user', item)
        self.assertIn('business_user', item)
        self.assertIn('title', item)
        self.assertIn('revisions', item)
        self.assertIn('delivery_time_in_days', item)
        self.assertIn('price', item)
        self.assertIn('features', item)
        self.assertIn('offer_type', item)
        self.assertIn('status', item)
        self.assertIn('created_at', item)
        self.assertIn('updated_at', item)
        self.assertEqual(item['id'], self.order.id)
        self.assertEqual(item['customer_user'], self.customer.id)
        self.assertEqual(item['business_user'], self.business.id)
        self.assertEqual(item['title'], 'Logo Design')
        self.assertEqual(item['revisions'], 3)
        self.assertEqual(item['delivery_time_in_days'], 5)
        self.assertEqual(item['price'], 150)
        self.assertEqual(item['features'], ['Logo Design', 'Visitenkarten'])
        self.assertEqual(item['offer_type'], 'basic')
        self.assertEqual(item['status'], 'in_progress')

    def test_get_orders_as_business_returns_same_order(self):
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], self.order.id)

    def test_get_orders_as_unrelated_user_returns_empty_list(self):
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.third_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data, [])

    # --- Unhappy path: 401 ---

    def test_get_orders_without_auth_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_orders_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
