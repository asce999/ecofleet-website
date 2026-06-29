import os
import django
import sys
from playwright.sync_api import sync_playwright, Error

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecofleet.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile, ToolRun, ToolRunFile
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Users
u1, _ = User.objects.get_or_create(username='p_user1')
u1.set_password('pw1')
u1.is_staff = True
u1.save()
UserProfile.objects.update_or_create(user=u1, defaults={'role': 'Employee', 'can_use_cof': True})

u2, _ = User.objects.get_or_create(username='p_user2')
u2.set_password('pw2')
u2.is_staff = True
u2.save()
UserProfile.objects.update_or_create(user=u2, defaults={'role': 'Employee', 'can_use_cof': True})

d1, _ = User.objects.get_or_create(username='p_director')
d1.set_password('pwd')
d1.is_staff = True
d1.save()
UserProfile.objects.update_or_create(user=d1, defaults={'role': 'Director', 'can_use_cof': True})

run = ToolRun.objects.create(user=u1, tool=ToolRun.TOOL_COF, status=ToolRun.STATUS_SUCCESS)
tf = ToolRunFile.objects.create(run=run, label="File1", file=SimpleUploadedFile("t.txt", b"test content"))

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # --- Context 1: User 1 ---
        context1 = browser.new_context(accept_downloads=True)
        page1 = context1.new_page()
        page1.goto("http://127.0.0.1:8000/portal/login/")
        page1.fill("input[name=username]", "p_user1")
        page1.fill("input[name=password]", "pw1")
        page1.click("button[type=submit]")
        
        resp = page1.goto(f"http://127.0.0.1:8000/portal/result/{run.pk}/")
        assert resp.status == 200, "Owner could not access result"
        
        try:
            with page1.expect_download():
                page1.goto(f"http://127.0.0.1:8000/portal/download/{tf.pk}/")
        except Error:
            pass # Download starts
        context1.close()
        
        # --- Context 2: User 2 ---
        context2 = browser.new_context(accept_downloads=True)
        page2 = context2.new_page()
        page2.goto("http://127.0.0.1:8000/portal/login/")
        page2.fill("input[name=username]", "p_user2")
        page2.fill("input[name=password]", "pw2")
        page2.click("button[type=submit]")
        
        resp = page2.goto(f"http://127.0.0.1:8000/portal/result/{run.pk}/")
        assert resp.status == 404, f"IDOR Vulnerability exists: User 2 accessed result! Status: {resp.status}"
        
        resp = page2.goto(f"http://127.0.0.1:8000/portal/download/{tf.pk}/")
        assert resp.status == 404, f"IDOR Vulnerability exists: User 2 accessed download! Status: {resp.status}"
        context2.close()
        
        # --- Context 3: Director ---
        context3 = browser.new_context(accept_downloads=True)
        page3 = context3.new_page()
        page3.goto("http://127.0.0.1:8000/portal/login/")
        page3.fill("input[name=username]", "p_director")
        page3.fill("input[name=password]", "pwd")
        page3.click("button[type=submit]")
        
        resp = page3.goto(f"http://127.0.0.1:8000/portal/result/{run.pk}/")
        assert resp.status == 200, "Director could not access result"
        
        try:
            with page3.expect_download():
                page3.goto(f"http://127.0.0.1:8000/portal/download/{tf.pk}/")
        except Error:
            pass # Download starts
        context3.close()
        
        browser.close()
        print("All Playwright Regression Tests Passed! IDOR successfully mitigated.")

if __name__ == '__main__':
    run_test()
