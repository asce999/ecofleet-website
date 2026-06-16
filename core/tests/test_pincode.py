from django.test import TestCase
from django.urls import reverse
from core.models import Pincode

class PincodeTestCase(TestCase):
    def setUp(self):
        # Create a small isolated fixture dataset
        Pincode.objects.get_or_create(pin="110001", defaults={"city": "New Delhi", "state": "Delhi", "location_type": "Non-ODA"})
        Pincode.objects.get_or_create(pin="175131", defaults={"city": "Manali", "state": "Himachal Pradesh", "location_type": "ODA"})

    def test_available_pincode(self):
        """1. Available Pincode: Verify known pincode returns available"""
        response = self.client.get(reverse('find_location'), {'pincode': '110001'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "110001")
        self.assertContains(response, "New Delhi")
        self.assertTrue(response.context['result']['found'])

    def test_unavailable_pincode(self):
        """2. Unavailable Pincode: Verify unknown pincode returns unavailable"""
        response = self.client.get(reverse('find_location'), {'pincode': '999999'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['result']['found'])
        self.assertContains(response, "Service Unavailable")

    def test_oda_rendering(self):
        """3. ODA Rendering: Verify ODA pincode displays correct location_type"""
        response = self.client.get(reverse('find_location'), {'pincode': '175131'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['result']['location_type'], "ODA")
        self.assertContains(response, "ODA")

    def test_non_oda_rendering(self):
        """4. Non-ODA Rendering: Verify Non-ODA pincode displays correct location_type"""
        response = self.client.get(reverse('find_location'), {'pincode': '110001'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['result']['location_type'], "Non-ODA")
        self.assertContains(response, "Non-ODA")

    def test_malformed_input(self):
        """5. Malformed Input: invalid, non-numeric, wrong length (no 500 errors)"""
        # Invalid / string input
        response1 = self.client.get(reverse('find_location'), {'pincode': 'abcdef'})
        self.assertEqual(response1.status_code, 200)
        self.assertFalse(response1.context['result']['found'])

        # Wrong length input
        response2 = self.client.get(reverse('find_location'), {'pincode': '123'})
        self.assertEqual(response2.status_code, 200)
        self.assertFalse(response2.context['result']['found'])

        # Special characters
        response3 = self.client.get(reverse('find_location'), {'pincode': '!@#$'})
        self.assertEqual(response3.status_code, 200)
        self.assertFalse(response3.context['result']['found'])

        # Empty input
        response4 = self.client.get(reverse('find_location'), {'pincode': ''})
        self.assertEqual(response4.status_code, 200)
        self.assertIsNone(response4.context['result'])
