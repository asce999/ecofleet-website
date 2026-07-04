from django.utils import timezone
from .base import BaseProvider, ProviderResult, CheckResult
from core.models import SalaryConfig

class SalaryProvider(BaseProvider):
    category = "Business Modules"
    key = "salary"
    title = "Salary Module"
    summary = "Salary calculation settings and health."

    def _fetch_data(self) -> ProviderResult:
        status = "healthy"
        checks = []
        metrics = {}
        
        config = SalaryConfig.objects.first()
        from core.models import EmployeeSalaryOverride
        overrides_count = EmployeeSalaryOverride.objects.count()
        metrics["Salary Overrides"] = overrides_count

        if config:
            checks.append(CheckResult(name="Configuration", status="healthy", message="Loaded"))
            metrics["Base Per Day"] = f"₹{config.basic_rate_per_day}" if config.basic_rate_per_day else "N/A"
            metrics["SP Allow Per Day"] = f"₹{config.sp_allowance_rate_per_day}" if config.sp_allowance_rate_per_day else "N/A"
        else:
            status = "warning"
            checks.append(CheckResult(name="Configuration", status="warning", message="Missing defaults"))

        return ProviderResult(
            status=status,
            health_score=100 if status == "healthy" else (80 if status == "warning" else 0),
            title=self.title,
            summary=self.summary,
            checks=checks,
            metrics=metrics
        )
