from django.contrib.auth import get_user_model
from django.utils import timezone
from .base import BaseProvider, ProviderResult, CheckResult
from core.models import UserProfile

User = get_user_model()

class BusinessProvider(BaseProvider):
    category = "Business Modules"
    key = "business"
    title = "Business Users"
    summary = "Platform user statistics and roles."
    cache_timeout = 300

    def _fetch_data(self) -> ProviderResult:
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
            checks.append(CheckResult(name="Directors", status="warning", message="No directors configured"))
        else:
            checks.append(CheckResult(name="Directors", status="healthy", message=f"{directors} loaded"))

        return ProviderResult(
            status=status,
            title=self.title,
            summary=self.summary,
            checks=checks,
            metrics=metrics,
            health_score=100 if status == "healthy" else (80 if status == "warning" else 0)
        )
