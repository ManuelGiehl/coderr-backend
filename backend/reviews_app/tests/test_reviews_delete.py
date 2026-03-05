"""
DELETE /api/reviews/{id}/ per spec:
204 = review deleted (creator only), 401 = not authenticated,
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


class ReviewDeleteEndpointTest(TestCase):
    """Tests for DELETE /api/reviews/{id}/ (only the creator can delete)."""

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
            description='To be deleted.',
        )
        self.url = f'/api/reviews/{self.review.id}/'

    # --- Happy path: 204 ---

    def test_delete_review_author_returns_204(self):
        response = self.client.delete(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_review_response_has_no_content(self):
        response = self.client.delete(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

    def test_delete_review_removes_from_db(self):
        review_id = self.review.id
        self.client.delete(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}',
        )
        self.assertFalse(Review.objects.filter(pk=review_id).exists())

    # --- Unhappy path: 401 ---

    def test_delete_review_without_auth_returns_401(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_review_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Unhappy path: 403 ---

    def test_delete_review_non_author_returns_403(self):
        response = self.client.delete(
            self.url,
            HTTP_AUTHORIZATION=f'Token {self.other_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Review.objects.filter(pk=self.review.id).exists())

    # --- Unhappy path: 404 ---

    def test_delete_review_not_found_returns_404(self):
        response = self.client.delete(
            '/api/reviews/99999/',
            HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
