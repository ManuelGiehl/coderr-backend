from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from offers_app.models import Offer, OfferDetail


class OfferListEndpointTest(TestCase):
    """
    GET /api/offers/ per spec:
    200 = paginated list, 400 = invalid request parameters.
    Happy and unhappy path tests; no auth required.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/offers/'
        self.user = User.objects.create_user(
            username='jdoe',
            first_name='John',
            last_name='Doe',
            email='jdoe@test.de',
            password='pass1234!',
        )
        self.offer = Offer.objects.create(
            user=self.user,
            title='Website Design',
            description='Professionelles Website-Design...',
        )
        OfferDetail.objects.create(
            offer=self.offer,
            price=Decimal('100.00'),
            delivery_time=7,
        )

    # --- Happy path: 200 ---

    def test_get_offers_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_offers_returns_paginated_structure(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('count', data)
        self.assertIn('next', data)
        self.assertIn('previous', data)
        self.assertIn('results', data)
        self.assertIsInstance(data['results'], list)

    def test_get_offers_results_have_required_fields(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertGreater(len(results), 0)
        item = results[0]
        for key in (
            'id', 'user', 'title', 'image', 'description',
            'created_at', 'updated_at', 'details',
            'min_price', 'min_delivery_time', 'user_details',
        ):
            self.assertIn(key, item)
        self.assertEqual(item['min_price'], 100.0)
        self.assertEqual(item['min_delivery_time'], 7)
        self.assertEqual(item['user_details']['username'], 'jdoe')
        self.assertEqual(item['user_details']['first_name'], 'John')
        self.assertEqual(item['user_details']['last_name'], 'Doe')

    def test_get_offers_filter_creator_id_returns_200(self):
        response = self.client.get(self.url, {'creator_id': self.user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

    def test_get_offers_ordering_returns_200(self):
        response = self.client.get(self.url, {'ordering': 'min_price'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(self.url, {'ordering': '-updated_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_offers_page_size_returns_200(self):
        response = self.client.get(self.url, {'page_size': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- Unhappy path: 400 ---

    def test_get_offers_invalid_creator_id_returns_400(self):
        response = self.client.get(self.url, {'creator_id': 'not_an_int'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('creator_id', response.json())

    def test_get_offers_invalid_min_price_returns_400(self):
        response = self.client.get(self.url, {'min_price': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('min_price', response.json())

    def test_get_offers_invalid_max_delivery_time_returns_400(self):
        response = self.client.get(
            self.url,
            {'max_delivery_time': 'not_int'},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('max_delivery_time', response.json())

    def test_get_offers_invalid_ordering_returns_400(self):
        response = self.client.get(self.url, {'ordering': 'invalid_field'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ordering', response.json())
