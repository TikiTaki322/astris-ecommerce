from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from django.contrib.auth import get_user_model

from datetime import timedelta

User = get_user_model()


class EmailVerificationViewTestCase(TestCase):
    def setUp(self):
        self.session = self.client.session
        self.session['pending_user'] = {
            'username': 'coralie',
            'email': 'coralie@example.com',
            'password': 'StrongPass123',
            'token': 'sweetBlonde321',
            'email_sent_at': (now() - timedelta(minutes=1)).isoformat(),
        }
        self.session.save()
        self.pending_user = self.session.get('pending_user')

    def test_valid_token_creates_user(self):
        self.client.get(f"{reverse('accounts:confirm_register')}?token={self.pending_user['token']}")

        user = User.objects.filter(email=self.pending_user['email']).first()
        self.assertIsNotNone(user)
        self.assertTrue(user.email_verified)
        self.assertNotIn('pending_user', self.client.session)  # session['pending_user'] was deleted after user creation

    def test_invalid_token_rejected(self):
        self.client.get(f"{reverse('accounts:confirm_register')}?token=MockToken")

        user = User.objects.filter(email=self.pending_user['email']).first()
        self.assertIsNone(user)
        self.assertNotIn('pending_user', self.client.session)  # session['pending_user'] was deleted after error

    def test_expired_token_rejected(self):
        self.session['pending_user']['email_sent_at'] = (now() - timedelta(minutes=12)).isoformat()
        self.session.save()
        self.pending_user = self.session.get('pending_user')
        self.client.get(f"{reverse('accounts:confirm_register')}?token={self.pending_user['token']}")

        user = User.objects.filter(email=self.pending_user['email']).first()
        self.assertIsNone(user)
        self.assertNotIn('pending_user', self.client.session)  # session['pending_user'] was deleted after error

