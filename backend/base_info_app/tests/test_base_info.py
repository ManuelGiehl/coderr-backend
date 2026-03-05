"""
GET /api/base-info/ per spec:
200 = platform stats (review_count, average_rating, business_profile_count, offer_count).
No auth required. Average rating rounded to one decimal.
All comments and docstrings in English.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from offers_app.models import Offer
from reviews_app.models import Review


class BaseInfoEndpointTest(TestCase):
    """Tests for GET /api/base-info/ (aggregate platform statistics)."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/base-info/'

    # --- Happy path: 200 ---

    def test_get_base_info_returns_200_without_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_base_info_response_structure(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('review_count', data)
        self.assertIn('average_rating', data)
        self.assertIn('business_profile_count', data)
        self.assertIn('offer_count', data)
        self.assertIsInstance(data['review_count'], int)
        self.assertIsInstance(data['offer_count'], int)
        self.assertIsInstance(data['business_profile_count'], int)
        self.assertIsInstance(data['average_rating'], (int, float))

    def test_get_base_info_empty_platform_returns_zeros(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['review_count'], 0)
        self.assertEqual(data['average_rating'], 0.0)
        self.assertEqual(data['business_profile_count'], 0)
        self.assertEqual(data['offer_count'], 0)

    def test_get_base_info_with_data_returns_correct_counts_and_average(self):
        business = User.objects.create_user(
            username='biz',
            email='biz@test.de',
            password='pass',
        )
        UserProfile.objects.create(user=business, user_type='business')
        Offer.objects.create(
            user=business,
            title='Offer 1',
            description='',
        )
        Offer.objects.create(
            user=business,
            title='Offer 2',
            description='',
        )
        customer = User.objects.create_user(
            username='cust',
            email='cust@test.de',
            password='pass',
        )
        Review.objects.create(
            business_user=business,
            reviewer=customer,
            rating=4,
            description='',
        )
        Review.objects.create(
            business_user=business,
            reviewer=customer,
            rating=5,
            description='',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['review_count'], 2)
        self.assertEqual(data['average_rating'], 4.5)
        self.assertEqual(data['business_profile_count'], 1)
        self.assertEqual(data['offer_count'], 2)

    def test_get_base_info_average_rating_rounded_to_one_decimal(self):
        business = User.objects.create_user(
            username='biz',
            email='biz@test.de',
            password='pass',
        )
        customer = User.objects.create_user(
            username='cust',
            email='cust@test.de',
            password='pass',
        )
        for r in (4, 4, 5):
            Review.objects.create(
                business_user=business,
                reviewer=customer,
                rating=r,
                description='',
            )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['review_count'], 3)
        self.assertEqual(data['average_rating'], 4.3)

    # --- Unhappy path: 405 (method not allowed for POST) ---

    def test_post_base_info_returns_405(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
