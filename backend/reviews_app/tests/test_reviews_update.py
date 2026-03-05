"""
PATCH /api/reviews/{id}/ per spec:
200 = review updated (author only), 400 = invalid data, 401 = not authenticated,
403 = not the creator, 404 = review not found.
All comments and docstrings in English.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from auth_app.models import UserProfile
from reviews_app.models import Review


class ReviewUpdateEndpointTest(TestCase):
    """Tests for PATCH /api/reviews/{id}/ (only rating and description; creator only)."""

    def setUp(self):
        self.client = APIClient()
        self.reviewer = User.objects.create_user(
            username='reviewer',
            email='reviewer@test.de',
            password='password1234',
        )
        UserProfile.objects.create(user=self.reviewer, user_type='customer')
        self.reviewer_token = Token.objects.create(user=self.reviewer)
        self.other_user = User.objects.create_user(
            username='other',
            email='other@test.de',
            password='password1234',
        )
        UserProfile.objects.create(user=self.other_user, user_type='customer')
        self.other_token = Token.objects.create(user=self.other_user)
        self.business = User.objects.create_user(
            username='business',
            email='business@test.de',
            password='password1234',
        )
        self.review = Review.objects.create(
            business_user=self.business,
            reviewer=self.reviewer,
            rating=4,
            description='Original text.',
        )
        self.url = f'/api/reviews/{self.review.id}/'

    # --- Happy path: 200 ---

    def test_patch_review_author_returns_200(self):
        response = self.client.patch(
            self.url,
            {'rating': 5, 'description': 'Noch besser als erwartet!'},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_review_response_updated_values(self):
        response = self.client.patch(
            self.url,
            {'rating': 5, 'description': 'Noch besser als erwartet!'},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['rating'], 5)
        self.assertEqual(data['description'], 'Noch besser als erwartet!')
        self.assertEqual(data['id'], self.review.id)
        self.assertEqual(data['business_user'], self.business.id)
        self.assertEqual(data['reviewer'], self.reviewer.id)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.description, 'Noch besser als erwartet!')

    def test_patch_review_partial_rating_only(self):
        response = self.client.patch(
            self.url,
            {'rating': 1},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['rating'], 1)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 1)
        self.assertEqual(self.review.description, 'Original text.')

    def test_patch_review_partial_description_only(self):
        response = self.client.patch(
            self.url,
            {'description': 'Updated description only.'},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()['description'],
            'Updated description only.',
        )
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 4)
        self.assertEqual(self.review.description, 'Updated description only.')

    # --- Unhappy path: 400 ---

    def test_patch_review_invalid_rating_returns_400(self):
        response = self.client.patch(
            self.url,
            {'rating': 10},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_review_rating_zero_returns_400(self):
        response = self.client.patch(
            self.url,
            {'rating': 0},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Unhappy path: 401 ---

    def test_patch_review_without_auth_returns_401(self):
        response = self.client.patch(
            self.url,
            {'rating': 5},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_review_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid')
        response = self.client.patch(
            self.url,
            {'rating': 5},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Unhappy path: 403 ---

    def test_patch_review_non_author_returns_403(self):
        response = self.client.patch(
            self.url,
            {'rating': 5},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.other_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 4)

    # --- Unhappy path: 404 ---

    def test_patch_review_not_found_returns_404(self):
        response = self.client.patch(
            '/api/reviews/99999/',
            {'rating': 5},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
