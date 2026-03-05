from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from orders_app.models import Order


class OrderUpdateEndpointTest(TestCase):
    """
    PATCH /api/orders/{id}/ per spec:
    200 = status updated (business owner only), 400 = invalid status,
    401 = not authenticated, 403 = not business / not order owner, 404 = order not found.
    """

    def setUp(self):
        self.client = APIClient()
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
        self.other_business = User.objects.create_user(
            username='other_business',
            email='other@test.de',
            password='password1234',
        )
        UserProfile.objects.create(user=self.other_business, user_type='business')
        self.other_business_token = Token.objects.create(user=self.other_business)
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

    # --- Happy path: 200 ---

    def test_patch_order_business_owner_returns_200(self):
        response = self.client.patch(
            self.url,
            {'status': 'completed'},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_order_status_updated_in_response_and_db(self):
        response = self.client.patch(
            self.url,
            {'status': 'completed'},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'completed')
        self.assertIn('updated_at', data)
        self.assertIn('id', data)
        self.assertEqual(data['title'], 'Logo Design')
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'completed')

    def test_patch_order_response_structure(self):
        response = self.client.patch(
            self.url,
            {'status': 'cancelled'},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        for key in (
            'id', 'customer_user', 'business_user', 'title', 'revisions',
            'delivery_time_in_days', 'price', 'features', 'offer_type',
            'status', 'created_at', 'updated_at',
        ):
            self.assertIn(key, data)
        self.assertEqual(data['status'], 'cancelled')

    def test_patch_order_allowed_statuses(self):
        for new_status in ('in_progress', 'completed', 'cancelled'):
            self.order.status = 'in_progress'
            self.order.save()
            response = self.client.patch(
                self.url,
                {'status': new_status},
                format='json',
                HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                f'PATCH with status={new_status} should return 200',
            )
            self.assertEqual(response.json()['status'], new_status)

    # --- Unhappy path: 400 ---

    def test_patch_order_invalid_status_returns_400(self):
        response = self.client.patch(
            self.url,
            {'status': 'invalid'},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_order_status_pending_returns_400(self):
        response = self.client.patch(
            self.url,
            {'status': 'pending'},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_order_empty_status_returns_400(self):
        response = self.client.patch(
            self.url,
            {'status': ''},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Unhappy path: 401 ---

    def test_patch_order_without_auth_returns_401(self):
        response = self.client.patch(
            self.url,
            {'status': 'completed'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_order_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid')
        response = self.client.patch(
            self.url,
            {'status': 'completed'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Unhappy path: 403 ---

    def test_patch_order_customer_returns_403(self):
        response = self.client.patch(
            self.url,
            {'status': 'completed'},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_order_other_business_returns_403(self):
        response = self.client.patch(
            self.url,
            {'status': 'completed'},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.other_business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Unhappy path: 404 ---

    def test_patch_order_not_found_returns_404(self):
        url = '/api/orders/99999/'
        response = self.client.patch(
            url,
            {'status': 'completed'},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
