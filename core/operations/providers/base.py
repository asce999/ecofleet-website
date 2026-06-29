import datetime
import logging
import traceback
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)

@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    status: str
    message: str

@dataclass(frozen=True, slots=True)
class ProviderResult:
    status: str
    title: str
    summary: str
    checks: List[CheckResult] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    health_score: int = 100
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    technical_details: Optional[str] = None
    last_updated: datetime.datetime = field(default_factory=timezone.now)

class BaseProvider:
    """
    Base interface for Operations Center Health Providers.
    Responsibility: Standardizes the return structure for health checks and gracefully handles exceptions.
    Inputs: Configuration params depending on the concrete implementation.
    Outputs: ProviderResult instance.
    Failure Behavior: Returns Critical status and logs the error without crashing the dashboard.
    """
    category: str = "Uncategorized"
    key: str = "unknown"
    title: str = "Base Provider"
    summary: str = ""
    cache_timeout: Optional[int] = None

    def get_data(self) -> ProviderResult:
        """
        Public method to safely execute the provider's logic.
        Catches any exception, logs it, and returns a CRITICAL failure response.
        """
        try:
            return self._fetch_data()
        except Exception as e:
            logger.error(f"Provider {self.__class__.__name__} failed: {e}")
            logger.debug(traceback.format_exc())
            return ProviderResult(
                status="unavailable",
                title=self.title,
                summary="Metrics temporarily unavailable.",
                checks=[CheckResult(name="Execution", status="critical", message="Service offline or misconfigured.")],
                health_score=0,
                technical_details=traceback.format_exc()
            )

    def _fetch_data(self) -> ProviderResult:
        """
        To be implemented by subclasses.
        Must return a ProviderResult instance.
        """
        raise NotImplementedError("Subclasses must implement _fetch_data()")
