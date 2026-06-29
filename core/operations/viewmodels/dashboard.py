import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass(frozen=True, slots=True)
class Insight:
    type: str  # e.g., 'success', 'warning', 'danger', 'info'
    icon: str  # e.g., 'ti-check', 'ti-alert-triangle'
    message: str

@dataclass(frozen=True, slots=True)
class SummaryCard:
    icon: str
    color: str
    text: str

@dataclass(frozen=True, slots=True)
class OperationalScore:
    score: int
    trend: str
    availability: Optional[str]
    active_alerts: int
    last_refresh: datetime.datetime
    last_incident: str

@dataclass(frozen=True, slots=True)
class QuickAction:
    title: str
    icon: str
    url: str
    permission: str

@dataclass(frozen=True, slots=True)
class ProviderDiagnostic:
    key: str
    title: str
    summary: str
    status: str
    health_score: int
    execution_duration: str
    checks: List[Dict[str, Any]]
    last_updated: datetime.datetime

@dataclass(frozen=True, slots=True)
class OperationsDashboard:
    operational_score: OperationalScore
    insights: List[Insight]
    executive_summary: List[SummaryCard]
    quick_actions: List[QuickAction]
    providers: List[ProviderDiagnostic]
    infrastructure: Dict[str, Any]
    business_modules: Dict[str, Any]
    kpi_metrics: Dict[str, Any]
    events: Any
