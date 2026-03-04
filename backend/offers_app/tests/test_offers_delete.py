from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from offers_app.models import Offer, OfferDetail


class OfferDeleteEndpointTest(TestCase):
    """
    DELETE /api/offers/{id}/ per spec:
    204 = deleted (no content), 401 = not authenticated,
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

    # --- Happy path: 204 No Content ---

    def test_delete_offer_as_owner_returns_204(self):
        response = self.client.delete(self.url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_offer_returns_no_content(self):
        response = self.client.delete(self.url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

    def test_delete_offer_removes_offer_and_details(self):
        offer_id = self.offer.id
        response = self.client.delete(self.url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Offer.objects.filter(pk=offer_id).exists())
        self.assertEqual(OfferDetail.objects.filter(offer_id=offer_id).count(), 0)

    # --- Unhappy path: 401 ---

    def test_delete_offer_without_auth_returns_401(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Offer.objects.filter(pk=self.offer.pk).exists())

    def test_delete_offer_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Offer.objects.filter(pk=self.offer.pk).exists())

    # --- Unhappy path: 403 (not owner) ---

    def test_delete_offer_as_non_owner_returns_403(self):
        response = self.client.delete(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.other_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Offer.objects.filter(pk=self.offer.pk).exists())

    # --- Unhappy path: 404 ---

    def test_delete_offer_nonexistent_id_returns_404(self):
        response = self.client.delete(
            '/api/offers/99999/',
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
