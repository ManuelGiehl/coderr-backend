from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from offers_app.models import Offer, OfferDetail


class OfferDetailRetrieveEndpointTest(TestCase):
    """
    GET /api/offerdetails/{id}/ per spec:
    200 = offer detail returned (title, price, delivery_time_in_days, features, offer_type),
    401 = not authenticated, 404 = not found.
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
        self.token = Token.objects.create(user=self.user)
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Token {self.token.key}'}
        self.offer = Offer.objects.create(
            user=self.user,
            title='Grafikdesign-Paket',
            description='Ein umfassendes Grafikdesign-Paket.',
        )
        self.detail = OfferDetail.objects.create(
            offer=self.offer,
            title='Basic Design',
            revisions=2,
            delivery_time=5,
            price=Decimal('100'),
            features=['Logo Design', 'Visitenkarte'],
            offer_type='basic',
        )
        self.url = f'/api/offerdetails/{self.detail.pk}/'

    # --- Happy path: 200 ---

    def test_get_offerdetail_by_id_authenticated_returns_200(self):
        response = self.client.get(self.url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_offerdetail_returns_expected_structure(self):
        response = self.client.get(self.url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertIn('revisions', data)
        self.assertIn('delivery_time_in_days', data)
        self.assertIn('price', data)
        self.assertIn('features', data)
        self.assertIn('offer_type', data)
        self.assertEqual(data['id'], self.detail.id)
        self.assertEqual(data['title'], 'Basic Design')
        self.assertEqual(data['revisions'], 2)
        self.assertEqual(data['delivery_time_in_days'], 5)
        self.assertEqual(data['price'], 100)
        self.assertEqual(data['features'], ['Logo Design', 'Visitenkarte'])
        self.assertEqual(data['offer_type'], 'basic')

    # --- Unhappy path: 401 ---

    def test_get_offerdetail_without_auth_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_offerdetail_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Unhappy path: 404 ---

    def test_get_offerdetail_nonexistent_id_returns_404(self):
        response = self.client.get(
            '/api/offerdetails/99999/',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
