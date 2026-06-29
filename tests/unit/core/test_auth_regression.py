from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import UserProfile, ToolRun, ToolRunFile
from django.core.files.uploadedfile import SimpleUploadedFile

class AuthRegressionTests(TestCase):
    def setUp(self):
        # Create a user who does NOT have permission for COF
        self.user_no_perms = User.objects.create_user(username='user_no_perms', password='pw1')
        self.user_no_perms.is_staff = True
        self.user_no_perms.save()
        UserProfile.objects.update_or_create(user=self.user_no_perms, defaults={'role': 'Employee', 'can_use_cof': False})

        self.client_no_perms = Client()
        self.client_no_perms.force_login(self.user_no_perms)

        # Create ToolRun and ToolRunFile owned by this user
        self.run = ToolRun.objects.create(
            user=self.user_no_perms,
            tool=ToolRun.TOOL_COF,
            status=ToolRun.STATUS_SUCCESS
        )
        self.file = ToolRunFile.objects.create(
            run=self.run,
            label="User File",
            file=SimpleUploadedFile("user.txt", b"user content")
        )

    def test_download_file_permission_failure_redirects(self):
        """
        Verify that if a user lacks permission for a tool, 
        downloading a file redirects rather than raising a NameError (500).
        """
        url = reverse('download_file', args=[self.file.pk])
        response = self.client_no_perms.get(url, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_tool_result_permission_failure_redirects(self):
        """
        Verify that if a user lacks permission for a tool, 
        viewing the tool result redirects rather than raising a NameError (500).
        """
        url = reverse('tool_result', args=[self.run.pk])
        response = self.client_no_perms.get(url, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))
