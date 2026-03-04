from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from offers_app.models import Offer, OfferDetail


def valid_offer_payload():
    return {
        'title': 'Grafikdesign-Paket',
        'image': None,
        'description': 'Ein umfassendes Grafikdesign-Paket für Unternehmen.',
        'details': [
            {
                'title': 'Basic Design',
                'revisions': 2,
                'delivery_time_in_days': 5,
                'price': 100,
                'features': ['Logo Design', 'Visitenkarte'],
                'offer_type': 'basic',
            },
            {
                'title': 'Standard Design',
                'revisions': 5,
                'delivery_time_in_days': 7,
                'price': 200,
                'features': ['Logo Design', 'Visitenkarte', 'Briefpapier'],
                'offer_type': 'standard',
            },
            {
                'title': 'Premium Design',
                'revisions': 10,
                'delivery_time_in_days': 10,
                'price': 500,
                'features': ['Logo Design', 'Visitenkarte', 'Briefpapier', 'Flyer'],
                'offer_type': 'premium',
            },
        ],
    }


class OfferCreateEndpointTest(TestCase):
    """
    POST /api/offers/ per spec:
    201 = created, 400 = invalid/incomplete details, 401 = not authenticated,
    403 = not business user.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/offers/'
        self.business_user = User.objects.create_user(
            username='business_user',
            email='biz@test.de',
            password='pass1234!',
        )
        UserProfile.objects.create(user=self.business_user, user_type='business')
        self.business_token = Token.objects.create(user=self.business_user)
        self.customer_user = User.objects.create_user(
            username='customer_user',
            email='cust@test.de',
            password='pass1234!',
        )
        UserProfile.objects.create(user=self.customer_user, user_type='customer')
        self.customer_token = Token.objects.create(user=self.customer_user)

    # --- Happy path: 201 ---

    def test_post_offers_business_user_returns_201(self):
        response = self.client.post(
            self.url,
            valid_offer_payload(),
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_offers_returns_offer_with_details(self):
        response = self.client.post(
            self.url,
            valid_offer_payload(),
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['title'], 'Grafikdesign-Paket')
        self.assertIn('details', data)
        self.assertEqual(len(data['details']), 3)
        self.assertEqual(data['details'][0]['title'], 'Basic Design')
        self.assertEqual(data['details'][0]['price'], 100)
        self.assertEqual(data['details'][0]['delivery_time_in_days'], 5)
        self.assertEqual(data['details'][0]['features'], ['Logo Design', 'Visitenkarte'])

    def test_post_offers_creates_offer_and_three_details(self):
        response = self.client.post(
            self.url,
            valid_offer_payload(),
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Offer.objects.count(), 1)
        self.assertEqual(OfferDetail.objects.count(), 3)

    # --- Unhappy path: 401 ---

    def test_post_offers_without_auth_returns_401(self):
        response = self.client.post(
            self.url,
            valid_offer_payload(),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Unhappy path: 403 (not business user) ---

    def test_post_offers_customer_user_returns_403(self):
        response = self.client.post(
            self.url,
            valid_offer_payload(),
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Offer.objects.count(), 0)

    # --- Unhappy path: 400 ---

    def test_post_offers_fewer_than_three_details_returns_400(self):
        payload = valid_offer_payload()
        payload['details'] = payload['details'][:2]
        response = self.client.post(
            self.url,
            payload,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('details', response.json())

    def test_post_offers_missing_title_returns_400(self):
        payload = valid_offer_payload()
        del payload['title']
        response = self.client.post(
            self.url,
            payload,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_offers_invalid_detail_price_returns_400(self):
        payload = valid_offer_payload()
        payload['details'][0]['price'] = -1
        response = self.client.post(
            self.url,
            payload,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
