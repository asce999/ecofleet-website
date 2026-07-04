from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import UserProfile, SystemEvent

User = get_user_model()

class SystemEventRequestIDTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123', is_staff=True)
        # Setup axes if needed (we just test standard auth)

    def test_system_event_request_id_on_login(self):
        response = self.client.post(reverse('portal_login'), {
            'username': 'testuser',
            'password': 'password123'
        })
        # Check if SystemEvent was created
        events = SystemEvent.objects.filter(event_type='user_login')
        self.assertTrue(events.exists())
        event = events.first()
        self.assertIsNotNone(event.request_id)
        self.assertNotEqual(event.request_id, '-')
