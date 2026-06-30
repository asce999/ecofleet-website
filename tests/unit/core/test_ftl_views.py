import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import FtlWorkbook
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class FtlViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='staff', password='pwd', is_staff=True)
        self.user.profile.can_use_ftl = True
        self.user.profile.save()
        self.client = Client()
        self.client.force_login(self.user)
        
        # Create dummy FTL workbook
        file = SimpleUploadedFile("dummy.xlsx", b"dummy_content")
        FtlWorkbook.objects.create(file=file, original_name="dummy.xlsx", is_active=True, active_sheet="Sheet1")

    @patch('core.views.ftl.os.path.exists', return_value=True)
    @patch('core.views.ftl.ftl_logic.get_ftl_row_values')
    def test_get_row_with_date_does_not_500(self, mock_get_row, mock_exists):
        # Mock the return value to contain a datetime object
        mock_get_row.return_value = {
            'row_num': 2,
            'booking_date': datetime.date(2026, 6, 15),
            'etd': datetime.datetime(2026, 6, 16, 10, 0),
            'lr_number': 'LR123'
        }
        
        url = reverse('ftl_api')
        response = self.client.get(url, {'action': 'get_row', 'row': '2'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        row_data = data.get('row_data', {})
        self.assertEqual(row_data.get('booking_date'), '2026-06-15')
        self.assertEqual(row_data.get('etd'), '2026-06-16')
