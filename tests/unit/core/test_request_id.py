from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import UserProfile, SystemEvent

User = get_user_model()

class RequestIDMiddlewareTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_request_id_header_presence(self):
        response = self.client.get(reverse('portal_login'))
        self.assertIn('X-Request-ID', response.headers)
        self.assertTrue(len(response.headers['X-Request-ID']) > 0)
