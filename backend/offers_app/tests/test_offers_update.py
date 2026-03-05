from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from offers_app.models import Offer, OfferDetail


def valid_update_details():
    """Three detail objects for PATCH details (same structure as create)."""
    return [
        {
            'title': 'Basic Design Updated',
            'revisions': 3,
            'delivery_time_in_days': 6,
            'price': 120,
            'features': ['Logo Design', 'Flyer'],
            'offer_type': 'basic',
        },
        {
            'title': 'Standard Design',
            'revisions': 5,
            'delivery_time_in_days': 10,
            'price': 120,
            'features': ['Logo Design', 'Visitenkarte', 'Briefpapier'],
            'offer_type': 'standard',
        },
        {
            'title': 'Premium Design',
            'revisions': 10,
            'delivery_time_in_days': 10,
            'price': 150,
            'features': ['Logo Design', 'Visitenkarte', 'Briefpapier', 'Flyer'],
            'offer_type': 'premium',
        },
    ]


class OfferUpdateEndpointTest(TestCase):
    """
    PATCH /api/offers/{id}/ per spec:
    200 = updated, 400 = invalid/incomplete details, 401 = not authenticated,
    403 = not offer owner, 404 = offer not found.
    """

    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username='test',
            first_name='test',
            last_name='test',
            email='test@test.de',
            password='password1234',
        )
        UserProfile.objects.create(user=self.owner, user_type='business')
        self.owner_token = Token.objects.create(user=self.owner)
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@test.de',
            password='password1234',
        )
        UserProfile.objects.create(user=self.other_user, user_type='business')
        self.other_token = Token.objects.create(user=self.other_user)

        self.offer = Offer.objects.create(
            user=self.owner,
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
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Token {self.owner_token.key}'}

    # --- Happy path: 200 ---

    def test_patch_offer_title_as_owner_returns_200(self):
        response = self.client.patch(
            self.url,
            {'title': 'Updated Grafikdesign-Paket'},
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['title'], 'Updated Grafikdesign-Paket')
        self.assertEqual(data['id'], self.offer.id)
        self.assertIn('details', data)
        self.assertEqual(len(data['details']), 3)

    def test_patch_offer_returns_full_offer_structure(self):
        response = self.client.patch(
            self.url,
            {'title': 'Updated Title'},
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertIn('image', data)
        self.assertIn('description', data)
        self.assertIn('details', data)
        for d in data['details']:
            self.assertIn('id', d)
            self.assertIn('title', d)
            self.assertIn('revisions', d)
            self.assertIn('delivery_time_in_days', d)
            self.assertIn('price', d)
            self.assertIn('features', d)
            self.assertIn('offer_type', d)

    def test_patch_offer_details_as_owner_returns_200(self):
        payload = {'details': valid_update_details()}
        response = self.client.patch(
            self.url,
            payload,
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['details'][0]['title'], 'Basic Design Updated')
        self.assertEqual(data['details'][0]['revisions'], 3)
        self.assertEqual(data['details'][0]['delivery_time_in_days'], 6)
        self.assertEqual(data['details'][0]['price'], 120)
        self.assertEqual(data['details'][0]['features'], ['Logo Design', 'Flyer'])
        self.assertEqual(data['details'][0]['offer_type'], 'basic')

    def test_patch_offer_partial_title_only_keeps_other_fields(self):
        response = self.client.patch(
            self.url,
            {'title': 'Only Title Changed'},
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.title, 'Only Title Changed')
        self.assertEqual(self.offer.description, 'Ein umfassendes Grafikdesign-Paket.')

    # --- Unhappy path: 401 ---

    def test_patch_offer_without_auth_returns_401(self):
        response = self.client.patch(
            self.url,
            {'title': 'Updated'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_offer_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid')
        response = self.client.patch(
            self.url,
            {'title': 'Updated'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Unhappy path: 403 (not owner) ---

    def test_patch_offer_as_non_owner_returns_403(self):
        response = self.client.patch(
            self.url,
            {'title': 'Hacked'},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.other_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.title, 'Grafikdesign-Paket')

    # --- Unhappy path: 404 ---

    def test_patch_offer_nonexistent_id_returns_404(self):
        response = self.client.patch(
            '/api/offers/99999/',
            {'title': 'Updated'},
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Unhappy path: 400 ---

    def test_patch_offer_two_details_updates_only_those(self):
        """Per spec: details can be updated individually; 1–3 elements allowed."""
        payload = {'details': valid_update_details()[:2]}
        response = self.client.patch(
            self.url,
            payload,
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['details'][0]['title'], 'Basic Design Updated')
        self.assertEqual(data['details'][1]['title'], 'Standard Design')
        self.assertEqual(len(data['details']), 3)
        for d in data['details']:
            self.assertIn('id', d)

    def test_patch_offer_detail_missing_offer_type_returns_400(self):
        """Per spec: offer_type must be sent to identify the detail; missing → 400."""
        details = [{
            'title': 'Basic Design Updated',
            'revisions': 3,
            'delivery_time_in_days': 5,
            'price': 100,
            'features': [],
        }]
        response = self.client.patch(
            self.url,
            {'details': details},
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('details', response.json())

    def test_patch_offer_invalid_detail_price_returns_400(self):
        details = valid_update_details()
        details[0]['price'] = -1
        response = self.client.patch(
            self.url,
            {'details': details},
            format='json',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
