from locust import HttpUser, task, between
from bs4 import BeautifulSoup

class EcoFleetUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login before starting tests"""
        # Get CSRF token
        response = self.client.get("/portal/login/")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
            if csrf_token:
                self.csrf_token = csrf_token.get('value')
                self.client.post("/portal/login/", {
                    "username": "admin", # Replace with actual load test user
                    "password": "password",
                    "csrfmiddlewaretoken": self.csrf_token
                })

    @task(3)
    def view_dashboard(self):
        self.client.get("/portal/")

    @task(1)
    def view_operations_center(self):
        self.client.get("/portal/operations-center/")

    @task(2)
    def view_attendance(self):
        self.client.get("/portal/attendance/")

    @task(2)
    def view_btpl(self):
        self.client.get("/portal/btpl/")

    @task(1)
    def view_cof(self):
        self.client.get("/portal/cof/")
