from django.conf import settings

import requests
import unittest


class ResendIntegrationTestCase(unittest.TestCase):
    """ Performance test of external mail service <resend.com> """

    @unittest.skipUnless(settings.RESEND_API_KEY and settings.RESEND_API_URL and settings.FROM_EMAIL, "Resend API not configured")
    def test_resend_api_email_delivery(self):
        payload = {
            'from': settings.FROM_EMAIL,
            'to': ['geyima7106@pngzero.com'],  # random temp. mail
            'subject': 'Test email from integration test',
            'html': '<p>Hello from integration test!</p>',
        }
        headers = {
            'Authorization': f'Bearer {settings.RESEND_API_KEY}',
            'Content-Type': 'application/json',
        }

        response = requests.post(settings.RESEND_API_URL, json=payload, headers=headers)
        print(f'Body: {response.text} | Status: {response.status_code}')
        self.assertIn(response.status_code, [200, 202], msg=f'Unexpected status: {response.status_code}')
