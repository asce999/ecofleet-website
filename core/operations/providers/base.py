import datetime
import logging
import traceback
from django.utils import timezone

logger = logging.getLogger('core.operations')

class BaseProvider:
    """
    Base interface for Operations Center Health Providers.
    Responsibility: Standardizes the return structure for health checks and gracefully handles exceptions.
    Inputs: Request (optional) or configuration params depending on the concrete implementation.
    Outputs: Dictionary with status, title, summary, checks, metrics, and last_updated.
    Failure Behavior: Returns Critical status and logs the error without crashing the dashboard.
    """
    
    def __init__(self, request=None):
        self.request = request
        self.title = "Base Provider"

    def get_data(self):
        """
        Public method to safely execute the provider's logic.
        Catches any exception, logs it, and returns a CRITICAL failure response.
        """
        try:
            return self._fetch_data()
        except Exception as e:
            logger.error(f"Provider {self.__class__.__name__} failed: {e}")
            logger.debug(traceback.format_exc())
            return {
                "status": "unavailable",
                "title": self.title,
                "summary": "Metrics temporarily unavailable.",
                "checks": [{"name": "Execution", "status": "critical", "message": "Service offline or misconfigured."}],
                "metrics": {},
                "warnings": [],
                "errors": [],
                "technical_details": traceback.format_exc(),
                "last_updated": timezone.now()
            }

    def _fetch_data(self):
        """
        To be implemented by subclasses.
        Must return a dictionary containing:
        - status: 'healthy', 'warning', or 'critical'
        - title: The display title of the provider
        - summary: A short text summary
        - checks: A list of dicts: {'name': str, 'status': str, 'message': str}
        - metrics: A dictionary of key-value pairs
        - last_updated: ISO formatted timestamp
        """
        raise NotImplementedError("Subclasses must implement _fetch_data()")
