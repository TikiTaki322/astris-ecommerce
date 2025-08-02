from django.test import TestCase
from django.urls import reverse

from unittest.mock import patch


class EmailSenderServiceTestCase(TestCase):
    @patch('accounts.services.email_sender.requests.post')
    def test_email_sent_and_session_updated(self, mock_post):
        # Configure mock response from <resend.com>
        mock_post.return_value.status_code = 202
        mock_post.return_value.text = 'Accepted'

        response = self.client.post(reverse('accounts:register'), {
            'username': 'testuser',
            'nickname': 'testuser',
            'email': 'testmail@example.com',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123'
        })

        self.assertRedirects(response, reverse('accounts:email_sent'))

        self.assertTrue(mock_post.called)
        _, kwargs = mock_post.call_args
        headers = kwargs['headers']
        payload = kwargs['json']

        self.assertIn('html', payload)
        self.assertIn('Authorization', headers)
        self.assertEqual(payload['to'], ['testmail@example.com'])

        session = self.client.session
        pending_user = session.get('pending_user')
        self.assertIsNotNone(pending_user)
        self.assertEqual(pending_user['email'], 'testmail@example.com')