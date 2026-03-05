from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from offers_app.models import Offer, OfferDetail
from orders_app.models import Order


class OrderCreateEndpointTest(TestCase):
    """
    POST /api/orders/ per spec:
    201 = order created from OfferDetail, 400 = invalid/missing offer_detail_id,
    401 = not authenticated, 403 = not customer, 404 = OfferDetail not found.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/orders/'
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
        self.offer = Offer.objects.create(
            user=self.business,
            title='Logo Design',
            description='Logo-Angebot',
        )
        self.offer_detail = OfferDetail.objects.create(
            offer=self.offer,
            title='Logo Design',
            revisions=3,
            delivery_time=5,
            price=Decimal('150'),
            features=['Logo Design', 'Visitenkarten'],
            offer_type='basic',
        )

    # --- Happy path: 201 ---

    def test_post_order_customer_returns_201(self):
        response = self.client.post(
            self.url,
            {'offer_detail_id': self.offer_detail.id},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_order_response_structure_and_values(self):
        response = self.client.post(
            self.url,
            {'offer_detail_id': self.offer_detail.id},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('id', data)
        self.assertIn('customer_user', data)
        self.assertIn('business_user', data)
        self.assertIn('title', data)
        self.assertIn('revisions', data)
        self.assertIn('delivery_time_in_days', data)
        self.assertIn('price', data)
        self.assertIn('features', data)
        self.assertIn('offer_type', data)
        self.assertIn('status', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertEqual(data['customer_user'], self.customer.id)
        self.assertEqual(data['business_user'], self.business.id)
        self.assertEqual(data['title'], 'Logo Design')
        self.assertEqual(data['revisions'], 3)
        self.assertEqual(data['delivery_time_in_days'], 5)
        self.assertEqual(data['price'], 150)
        self.assertEqual(data['features'], ['Logo Design', 'Visitenkarten'])
        self.assertEqual(data['offer_type'], 'basic')
        self.assertEqual(data['status'], 'in_progress')

    def test_post_order_creates_order_in_db(self):
        self.assertEqual(Order.objects.count(), 0)
        self.client.post(
            self.url,
            {'offer_detail_id': self.offer_detail.id},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.get()
        self.assertEqual(order.customer_user_id, self.customer.id)
        self.assertEqual(order.business_user_id, self.business.id)
        self.assertEqual(order.title, 'Logo Design')
        self.assertEqual(order.status, 'in_progress')

    # --- Unhappy path: 400 ---

    def test_post_order_missing_offer_detail_id_returns_400(self):
        response = self.client.post(
            self.url,
            {},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_order_invalid_offer_detail_id_returns_400(self):
        response = self.client.post(
            self.url,
            {'offer_detail_id': 'invalid'},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_order_zero_offer_detail_id_returns_400(self):
        response = self.client.post(
            self.url,
            {'offer_detail_id': 0},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Unhappy path: 401 ---

    def test_post_order_without_auth_returns_401(self):
        response = self.client.post(
            self.url,
            {'offer_detail_id': self.offer_detail.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_order_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid')
        response = self.client.post(
            self.url,
            {'offer_detail_id': self.offer_detail.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Unhappy path: 403 ---

    def test_post_order_business_user_returns_403(self):
        response = self.client.post(
            self.url,
            {'offer_detail_id': self.offer_detail.id},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Unhappy path: 404 ---

    def test_post_order_nonexistent_offer_detail_returns_404(self):
        nonexistent_id = 99999
        self.assertFalse(
            OfferDetail.objects.filter(pk=nonexistent_id).exists(),
        )
        response = self.client.post(
            self.url,
            {'offer_detail_id': nonexistent_id},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
