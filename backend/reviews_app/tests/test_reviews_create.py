"""
POST /api/reviews/ per spec:
201 = review created (customer only), 400 = bad request / duplicate review, 401 = not authenticated,
403 = not customer (business user).
All comments and docstrings in English.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from reviews_app.models import Review


class ReviewCreateEndpointTest(TestCase):
    """Tests for POST /api/reviews/ (create review; customer only; one per business user)."""

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
        self.url = '/api/reviews/'
        self.valid_payload = {
            'business_user': self.business.id,
            'rating': 4,
            'description': 'Alles war toll!',
        }

    # --- Happy path: 201 ---

    def test_post_review_customer_returns_201(self):
        response = self.client.post(
            self.url,
            self.valid_payload,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_review_response_structure_and_values(self):
        response = self.client.post(
            self.url,
            self.valid_payload,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        for key in (
            'id', 'business_user', 'reviewer', 'rating',
            'description', 'created_at', 'updated_at',
        ):
            self.assertIn(key, data)
        self.assertEqual(data['business_user'], self.business.id)
        self.assertEqual(data['reviewer'], self.customer.id)
        self.assertEqual(data['rating'], 4)
        self.assertEqual(data['description'], 'Alles war toll!')

    def test_post_review_creates_in_db(self):
        self.assertEqual(Review.objects.count(), 0)
        self.client.post(
            self.url,
            self.valid_payload,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.get()
        self.assertEqual(review.business_user_id, self.business.id)
        self.assertEqual(review.reviewer_id, self.customer.id)
        self.assertEqual(review.rating, 4)

    # --- Unhappy path: 400 ---

    def test_post_review_missing_business_user_returns_400(self):
        payload = {'rating': 4, 'description': 'Good'}
        response = self.client.post(
            self.url,
            payload,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_review_invalid_rating_returns_400(self):
        payload = {**self.valid_payload, 'rating': 10}
        response = self.client.post(
            self.url,
            payload,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_review_nonexistent_business_user_returns_400(self):
        payload = {**self.valid_payload, 'business_user': 99999}
        response = self.client.post(
            self.url,
            payload,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Unhappy path: 401 ---

    def test_post_review_without_auth_returns_401(self):
        response = self.client.post(
            self.url,
            self.valid_payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_review_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid')
        response = self.client.post(
            self.url,
            self.valid_payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Unhappy path: 403 ---

    def test_post_review_business_user_returns_403(self):
        response = self.client.post(
            self.url,
            self.valid_payload,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.business_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_review_duplicate_same_business_returns_400(self):
        """Duplicate review (same customer, same business) returns 400 Bad Request per spec."""
        Review.objects.create(
            business_user=self.business,
            reviewer=self.customer,
            rating=3,
            description='First.',
        )
        response = self.client.post(
            self.url,
            self.valid_payload,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.customer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Review.objects.filter(reviewer=self.customer).count(), 1)
