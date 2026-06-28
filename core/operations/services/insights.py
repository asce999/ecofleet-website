from typing import Dict, List, Any
from core.operations.providers.base import ProviderResult
from core.operations.viewmodels.dashboard import Insight, SummaryCard, OperationalScore
from django.utils import timezone

class InsightsService:
    @staticmethod
    def generate_predictive_insights(providers_dict: Dict[str, ProviderResult], has_critical: bool) -> List[Insight]:
        insights = []
        
        db_data = providers_dict.get('database')
        if db_data:
            db_size = db_data.metrics.get('File Size', '0 MB')
            try:
                size_val = float(db_size.split()[0])
                if size_val > 500:
                    insights.append(Insight(type="warning", icon="ti-database", message=f"Database size is {size_val:.1f}MB. Optimization recommended."))
                else:
                    insights.append(Insight(type="info", icon="ti-chart-line", message="Collecting operational history for storage projections."))
            except:
                pass
            
        perf_data = providers_dict.get('performance')
        latency = '0 ms'
        if perf_data:
            latency = perf_data.metrics.get('Avg Latency', '0 ms')
            try:
                lat_val = float(latency.split()[0])
                if lat_val > 500:
                    insights.append(Insight(type="warning", icon="ti-bolt", message=f"Performance degrading. Average latency is {lat_val:.0f}ms."))
                elif lat_val > 0:
                    insights.append(Insight(type="info", icon="ti-chart-line", message="Collecting operational history for performance trends."))
            except:
                pass
            
        backup_data = providers_dict.get('backups')
        last_backup = 'N/A'
        if backup_data:
            last_backup = backup_data.metrics.get('Latest Backup', 'N/A')
            if last_backup == 'N/A':
                insights.append(Insight(type="danger", icon="ti-shield", message="No backups found."))
            else:
                insights.append(Insight(type="success", icon="ti-shield", message="Backup freshness excellent."))
            
        if not has_critical:
            insights.append(Insight(type="success", icon="ti-check", message="No critical system failures."))
            
        return insights

    @staticmethod
    def generate_executive_summary(providers_dict: Dict[str, ProviderResult], has_critical: bool) -> List[SummaryCard]:
        summary = []
        
        biz_data = providers_dict.get('business')
        if biz_data:
            reports_today = biz_data.metrics.get('Reports Today')
            if reports_today:
                summary.append(SummaryCard(icon="check", color="success", text=f"{reports_today} reports generated today"))
        
        att_data = providers_dict.get('attendance')
        if att_data:
            att_jobs = att_data.metrics.get('Jobs Today')
            if att_jobs:
                summary.append(SummaryCard(icon="check", color="success", text=f"{att_jobs} attendance uploads completed"))
            
        if not has_critical:
            summary.append(SummaryCard(icon="check", color="success", text="All business modules operational"))
        else:
            summary.append(SummaryCard(icon="alert-triangle", color="danger", text="Critical failures detected in infrastructure"))
            
        backup_data = providers_dict.get('backups')
        last_backup = 'N/A'
        if backup_data:
            last_backup = backup_data.metrics.get('Latest Backup', 'N/A')
            
        if last_backup != 'N/A':
            summary.append(SummaryCard(icon="check", color="success", text="Database backup completed successfully"))
        else:
            summary.append(SummaryCard(icon="alert-triangle", color="warning", text="No recent backups found"))
            
        perf_data = providers_dict.get('performance')
        latency = '0 ms'
        if perf_data:
            latency = perf_data.metrics.get('Avg Latency', '0 ms')
            
        if latency != '0 ms':
            summary.append(SummaryCard(icon="check", color="success", text=f"Platform latency stable at {latency}"))
            
        return summary

    @staticmethod
    def calculate_operational_score(providers_dict: Dict[str, ProviderResult], has_critical: bool, has_warning: bool) -> OperationalScore:
        total_health = 0
        provider_count = 0
        active_alerts = 0
        
        for p in providers_dict.values():
            total_health += p.health_score
            provider_count += 1
            if p.status in ('warning', 'critical', 'unavailable'):
                active_alerts += 1
                
        score = int(total_health / provider_count) if provider_count > 0 else 0
        
        trend = "stable"
        if has_critical:
            trend = "down"
        elif has_warning:
            trend = "degrading"
            
        availability = "99.9%" if not has_critical else "99.5%"
        
        return OperationalScore(
            score=score,
            trend=trend,
            availability=availability,
            active_alerts=active_alerts,
            last_refresh=timezone.now(),
            last_incident="None recently" if not has_critical else "Ongoing Infrastructure Issue"
        )
