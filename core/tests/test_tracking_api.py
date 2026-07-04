from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch

class TrackingAPITest(TestCase):
    def setUp(self):
        self.client = Client()

    @patch('core.services.tracking.requests.post')
    def test_tracking_api_success(self, mock_post):
        # Mock external API response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "status": "true",
            "message": ["Docket Info"],
            "data": {
                "info": {
                    "forwording_no": "12345",
                    "origin": "PUNE",
                    "Destination": "MUMBAI"
                },
                "trackinfo": []
            }
        }
        
        url = reverse('api_tracking', args=['12345'])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "true")
        self.assertEqual(data["data"]["info"]["origin"], "PUNE")
        
    @patch('core.services.tracking.requests.post')
    def test_tracking_api_failure(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "status": "false",
            "message": "Not Found"
        }
        
        url = reverse('api_tracking', args=['99999'])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
