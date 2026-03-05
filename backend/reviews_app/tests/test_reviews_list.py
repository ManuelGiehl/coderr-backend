"""
GET /api/reviews/ per spec:
200 = list of reviews (filtered/sorted by query params), 401 = not authenticated.
All comments and docstrings in English.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from reviews_app.models import Review


class ReviewListEndpointTest(TestCase):
    """Tests for GET /api/reviews/ (list, filter by business_user_id/reviewer_id, ordering)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.de',
            password='password1234',
        )
        self.token = Token.objects.create(user=self.user)
        self.business = User.objects.create_user(
            username='business',
            email='business@test.de',
            password='password1234',
        )
        self.reviewer = User.objects.create_user(
            username='reviewer',
            email='reviewer@test.de',
            password='password1234',
        )
        self.review1 = Review.objects.create(
            business_user=self.business,
            reviewer=self.reviewer,
            rating=4,
            description='Sehr professioneller Service.',
        )
        self.review2 = Review.objects.create(
            business_user=self.business,
            reviewer=self.reviewer,
            rating=5,
            description='Top Qualität und schnelle Lieferung!',
        )
        self.url = '/api/reviews/'

    # --- Happy path: 200 ---

    def test_get_reviews_authenticated_returns_200(self):
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_reviews_returns_list_structure(self):
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        item = data[0]
        for key in (
            'id', 'business_user', 'reviewer', 'rating',
            'description', 'created_at', 'updated_at',
        ):
            self.assertIn(key, item)
        self.assertEqual(item['business_user'], self.business.id)
        self.assertEqual(item['reviewer'], self.reviewer.id)
        self.assertIn(item['rating'], (4, 5))
        self.assertIn(item['description'], (
            'Sehr professioneller Service.',
            'Top Qualität und schnelle Lieferung!',
        ))

    def test_get_reviews_filter_by_business_user_id(self):
        other_business = User.objects.create_user(
            username='other_biz',
            email='other@test.de',
            password='password1234',
        )
        Review.objects.create(
            business_user=other_business,
            reviewer=self.reviewer,
            rating=3,
            description='Other.',
        )
        response = self.client.get(
            f'{self.url}?business_user_id={self.business.id}',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        for item in data:
            self.assertEqual(item['business_user'], self.business.id)

    def test_get_reviews_filter_by_reviewer_id(self):
        other_reviewer = User.objects.create_user(
            username='other_rev',
            email='rev@test.de',
            password='password1234',
        )
        Review.objects.create(
            business_user=self.business,
            reviewer=other_reviewer,
            rating=1,
            description='From other.',
        )
        response = self.client.get(
            f'{self.url}?reviewer_id={self.reviewer.id}',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        for item in data:
            self.assertEqual(item['reviewer'], self.reviewer.id)

    def test_get_reviews_ordering_by_rating(self):
        response = self.client.get(
            f'{self.url}?ordering=rating',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['rating'], 4)
        self.assertEqual(data[1]['rating'], 5)

    def test_get_reviews_ordering_by_updated_at(self):
        response = self.client.get(
            f'{self.url}?ordering=updated_at',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)

    def test_get_reviews_empty_list_returns_200(self):
        Review.objects.all().delete()
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    # --- Unhappy path: 401 ---

    def test_get_reviews_without_auth_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_reviews_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
