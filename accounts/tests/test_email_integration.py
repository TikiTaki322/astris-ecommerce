from accounts.services.email_sender import RESEND_API_URL, RESEND_API_KEY, FROM_EMAIL

import requests
import unittest


class ResendIntegrationTestCase(unittest.TestCase):
    """ Performance test of external mail service <resend.com> """

    @unittest.skipUnless(RESEND_API_KEY and RESEND_API_URL and FROM_EMAIL, "Resend API not configured")
    def test_resend_api_email_delivery(self):
        payload = {
            'from': FROM_EMAIL,
            'to': ['geyima7106@pngzero.com'],  # random temp. mail
            'subject': 'Test email from integration test',
            'html': '<p>Hello from integration test!</p>',
        }
        headers = {
            'Authorization': f'Bearer {RESEND_API_KEY}',
            'Content-Type': 'application/json',
        }

        response = requests.post(RESEND_API_URL, json=payload, headers=headers)
        print(f'Body: {response.text} | Status: {response.status_code}')
        self.assertIn(response.status_code, [200, 202], msg=f'Unexpected status: {response.status_code}')
