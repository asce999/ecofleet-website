from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import UserProfile, ToolRun, ToolRunFile
from django.core.files.uploadedfile import SimpleUploadedFile

class ProviderAuthorizationTests(TestCase):
    def setUp(self):
        # Create normal employee 1
        self.user1 = User.objects.create_user(username='user1', password='pw1')
        self.user1.is_staff = True
        self.user1.save()
        UserProfile.objects.update_or_create(user=self.user1, defaults={'role': 'Employee', 'can_use_cof': True})

        # Create normal employee 2
        self.user2 = User.objects.create_user(username='user2', password='pw2')
        self.user2.is_staff = True
        self.user2.save()
        UserProfile.objects.update_or_create(user=self.user2, defaults={'role': 'Employee', 'can_use_cof': True})

        # Create Director
        self.director = User.objects.create_user(username='director', password='pwd')
        self.director.is_staff = True
        self.director.save()
        UserProfile.objects.update_or_create(user=self.director, defaults={'role': 'Director', 'can_use_cof': True})

        # Create authenticated clients
        self.client1 = Client()
        self.client1.force_login(self.user1)

        self.client2 = Client()
        self.client2.force_login(self.user2)

        self.client_director = Client()
        self.client_director.force_login(self.director)

        # Create ToolRuns and ToolRunFiles for User 1
        self.run1 = ToolRun.objects.create(
            user=self.user1,
            tool=ToolRun.TOOL_COF,
            status=ToolRun.STATUS_SUCCESS
        )
        self.file1 = ToolRunFile.objects.create(
            run=self.run1,
            label="User 1 File",
            file=SimpleUploadedFile("user1.txt", b"user 1 content")
        )

        # Create ToolRuns and ToolRunFiles for User 2
        self.run2 = ToolRun.objects.create(
            user=self.user2,
            tool=ToolRun.TOOL_COF,
            status=ToolRun.STATUS_SUCCESS
        )
        self.file2 = ToolRunFile.objects.create(
            run=self.run2,
            label="User 2 File",
            file=SimpleUploadedFile("user2.txt", b"user 2 content")
        )

    def test_queryset_for_user_normal(self):
        runs_user1 = list(ToolRun.objects.for_user(self.user1))
        self.assertEqual(len(runs_user1), 1)
        self.assertEqual(runs_user1[0], self.run1)

    def test_queryset_for_user_director(self):
        self.director.refresh_from_db()
        runs_director = list(ToolRun.objects.for_user(self.director))
        self.assertEqual(len(runs_director), 2)
        self.assertIn(self.run1, runs_director)
        self.assertIn(self.run2, runs_director)

    def test_download_file_isolation(self):
        url = reverse('download_file', args=[self.file2.pk])
        response = self.client1.get(url)
        self.assertEqual(response.status_code, 404)
        response = self.client2.get(url)
        self.assertEqual(response.status_code, 200)

    def test_download_file_director_access(self):
        url = reverse('download_file', args=[self.file2.pk])
        response = self.client_director.get(url)
        self.assertEqual(response.status_code, 200)

    def test_tool_result_isolation(self):
        url = reverse('tool_result', args=[self.run2.pk])
        response = self.client1.get(url)
        self.assertEqual(response.status_code, 404)
        response = self.client2.get(url)
        self.assertEqual(response.status_code, 200)
