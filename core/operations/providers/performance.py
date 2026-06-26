from django.core.cache import cache
from django.utils import timezone
from .base import BaseProvider

class PerformanceProvider(BaseProvider):
    def __init__(self, request=None):
        super().__init__(request)
        self.title = "Performance metrics"

    def _fetch_data(self):
        status = "healthy"
        checks = []
        metrics_dict = {}
        
        # Fetch from LocMemCache
        data = cache.get('performance_metrics')
        if not data:
            return {
                "status": "warning",
                "health_score": 50,
                "title": self.title,
                "summary": "No performance data available yet. Make some requests.",
                "checks": [{"name": "Cache", "status": "warning", "message": "Empty"}],
                "metrics": {"Total Requests": 0, "Avg Latency": "N/A", "Max Latency": "N/A", "95th Percentile": "N/A"},
                "warnings": [],
                "errors": [],
                "technical_details": None,
                "last_updated": timezone.now()
            }
            
        requests = data.get('requests', 0)
        total_time = data.get('total_time', 0.0)
        min_time = data.get('min_time', 0.0)
        max_time = data.get('max_time', 0.0)
        recent_times = data.get('recent_times', [])
        
        if requests > 0:
            avg = total_time / requests
            metrics_dict["Total Requests"] = requests
            metrics_dict["Avg Latency"] = f"{avg:.2f} ms"
            metrics_dict["Max Latency"] = f"{max_time:.2f} ms"
            metrics_dict["Slowest Endpoint"] = data.get('slowest_endpoint', 'None')
            
            if recent_times:
                recent_chronological = list(recent_times)
                sorted_times = sorted(recent_times)
                p95_idx = int(len(sorted_times) * 0.95)
                if p95_idx >= len(sorted_times):
                    p95_idx = len(sorted_times) - 1
                p95 = sorted_times[p95_idx]
                metrics_dict["95th Percentile"] = f"{p95:.2f} ms"
                
                if p95 > 1000: # 1 second
                    status = "warning"
                    checks.append({"name": "P95 Latency", "status": "warning", "message": "> 1000ms"})
                else:
                    checks.append({"name": "P95 Latency", "status": "healthy", "message": "OK (< 1000ms)"})
                
                # Chart data for response times (up to last 15 requests)
                chart_len = min(len(recent_chronological), 15)
                metrics_dict["labels"] = [f"Req {i+1}" for i in range(chart_len)]
                metrics_dict["data"] = [round(x, 1) for x in recent_chronological[-chart_len:]]
            else:
                metrics_dict["labels"] = []
                metrics_dict["data"] = []
        else:
            checks.append({"name": "Requests", "status": "warning", "message": "0 logged"})
            metrics_dict["labels"] = []
            metrics_dict["data"] = []
            
        return {
            "status": status,
            "title": self.title,
            "summary": "Rolling endpoint performance metrics.",
            "checks": checks,
            "metrics": metrics_dict,
            "health_score": 100 if status == "healthy" else (80 if status == "warning" else 0),
            "warnings": [],
            "errors": [],
            "technical_details": None,
            "last_updated": timezone.now()
        }
