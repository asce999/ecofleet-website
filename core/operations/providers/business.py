from django.contrib.auth import get_user_model
from django.utils import timezone
from .base import BaseProvider
from core.models import UserProfile

User = get_user_model()

class BusinessProvider(BaseProvider):
    def __init__(self, request=None):
        super().__init__(request)
        self.title = "Business Users"

    def _fetch_data(self):
        status = "healthy"
        checks = []
        metrics = {}
        
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        directors = UserProfile.objects.filter(role='Director').count()
        
        metrics["Total Users"] = total_users
        metrics["Enabled Accounts"] = active_users
        metrics["Directors"] = directors
        
        if directors == 0:
            status = "warning"
            checks.append({"name": "Directors", "status": "warning", "message": "No directors configured"})
        else:
            checks.append({"name": "Directors", "status": "healthy", "message": f"{directors} loaded"})

        return {
            "status": status,
            "title": self.title,
            "summary": "Platform user statistics and roles.",
            "checks": checks,
            "metrics": metrics,
            "health_score": 100 if status == "healthy" else (80 if status == "warning" else 0),
            "warnings": [],
            "errors": [],
            "technical_details": None,
            "last_updated": timezone.now()
        }
