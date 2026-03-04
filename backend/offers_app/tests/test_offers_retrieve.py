from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from offers_app.models import Offer, OfferDetail


class OfferRetrieveEndpointTest(TestCase):
    """
    GET /api/offers/{id}/ per spec:
    200 = offer details returned, 401 = not authenticated, 404 = not found.
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
        for i, (title, price, days) in enumerate([
            ('Basic', 50, 5),
            ('Standard', 100, 7),
            ('Premium', 200, 10),
        ]):
            OfferDetail.objects.create(
                offer=self.offer,
                title=title,
                revisions=2 + i,
                delivery_time=days,
                price=Decimal(str(price)),
                features=[],
                offer_type=['basic', 'standard', 'premium'][i],
            )
        self.url = f'/api/offers/{self.offer.pk}/'

    # --- Happy path: 200 ---

    def test_get_offer_by_id_authenticated_returns_200(self):
        response = self.client.get(self.url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_offer_by_id_returns_expected_structure(self):
        response = self.client.get(self.url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('id', data)
        self.assertIn('user', data)
        self.assertIn('title', data)
        self.assertIn('image', data)
        self.assertIn('description', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('details', data)
        self.assertIn('min_price', data)
        self.assertIn('min_delivery_time', data)
        self.assertEqual(data['id'], self.offer.id)
        self.assertEqual(data['user'], self.user.id)
        self.assertEqual(data['title'], 'Grafikdesign-Paket')
        self.assertEqual(data['min_price'], 50.0)
        self.assertEqual(data['min_delivery_time'], 5)
        self.assertEqual(len(data['details']), 3)
        for d in data['details']:
            self.assertIn('id', d)
            self.assertIn('url', d)

    # --- Unhappy path: 401 ---

    def test_get_offer_by_id_without_auth_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_offer_by_id_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Unhappy path: 404 ---

    def test_get_offer_by_nonexistent_id_returns_404(self):
        response = self.client.get(
            '/api/offers/99999/',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
