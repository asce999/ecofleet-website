import os
from django.conf import settings
from django.http import JsonResponse
from django.db import connection
from django.db.utils import OperationalError
from django.core.cache import cache

from django.utils import timezone
from core.decorators import staff_required

def health_check(request):
    status = {
        'status': 'ok',
        'components': {
            'django': 'ok',
            'database': 'unknown',
            'media': 'unknown',
            'static': 'unknown'
        }
    }

    # 1. Database
    try:
        connection.ensure_connection()
        status['components']['database'] = 'ok'
    except OperationalError:
        status['components']['database'] = 'error'
        status['status'] = 'error'

    # 2. Media Directory
    media_path = settings.MEDIA_ROOT
    if os.path.exists(media_path) and os.access(media_path, os.W_OK):
        status['components']['media'] = 'ok'
    else:
        status['components']['media'] = 'error'
        status['status'] = 'error'

    # 3. Static Directory
    static_path = settings.STATIC_ROOT
    if not static_path:
        static_path = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None
    
    if static_path and os.path.exists(static_path):
        status['components']['static'] = 'ok'
    else:
        # In development STATIC_ROOT might not exist yet, so we just warn or ok if DIRS exists
        status['components']['static'] = 'warning'



    # Final response
    http_status = 200 if status['status'] == 'ok' else 503
    return JsonResponse(status, status=http_status)


@staff_required
def sentry_debug(request):
    if not settings.DEBUG:
        from django.http import Http404
        raise Http404("Not found")
    
    # This will trigger an unhandled exception for Sentry to capture
    division_by_zero = 1 / 0
    return JsonResponse({"status": "unreachable"})

from django.shortcuts import render
from core.models import SystemEvent
import pkgutil
import importlib
import inspect
from core.operations.providers.base import BaseProvider, ProviderResult, CheckResult

_PROVIDER_CLASSES_CACHE = None

@staff_required
def operations_center(request):
    """
    Operations Center Dashboard.
    Thin view that acts as an orchestrator.
    """
    from core.operations.services.insights import InsightsService
    from core.operations.viewmodels.dashboard import (
        OperationsDashboard, QuickAction, ProviderDiagnostic
    )
    
    providers_dict = {}
    has_critical = False
    has_warning = False
    
    # 1. Discover Providers
    global _PROVIDER_CLASSES_CACHE
    if _PROVIDER_CLASSES_CACHE is None:
        _PROVIDER_CLASSES_CACHE = []
        import core.operations.providers as provider_package
        for _, module_name, _ in pkgutil.iter_modules(provider_package.__path__):
            if module_name == 'base':
                continue
            full_module_name = f"{provider_package.__name__}.{module_name}"
            try:
                module = importlib.import_module(full_module_name)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseProvider) and obj is not BaseProvider:
                        _PROVIDER_CLASSES_CACHE.append(obj)
            except Exception as e:
                # Add a dummy class or just log it; the previous code generated a failed result here
                pass # We handle instantiation later
                
    import core.operations.providers as provider_package
    for _, module_name, _ in pkgutil.iter_modules(provider_package.__path__):
        if module_name == 'base':
            continue
        full_module_name = f"{provider_package.__name__}.{module_name}"
        try:
            # Re-discover to get errors for UI, but skip loading if already in cache
            module = importlib.import_module(full_module_name)
        except Exception as e:
            fallback = ProviderResult(
                status="unavailable",
                health_score=0,
                title=f"Provider Module: {module_name}",
                summary="Failed to load provider module.",
                checks=[CheckResult(name="Load", status="critical", message=str(e))],
                metrics={},
                technical_details=str(e)
            )
            providers_dict[f"failed_{module_name}"] = fallback
            has_critical = True

    for provider_class in _PROVIDER_CLASSES_CACHE:
        try:
            provider_instance = provider_class()
            cache_key = f"opscenter_provider_{provider_instance.key}"
            
            data = None
            if provider_instance.cache_timeout:
                data = cache.get(cache_key)
                
            if data is None:
                data = provider_instance.get_data()
                if provider_instance.cache_timeout:
                    cache.set(cache_key, data, provider_instance.cache_timeout)
            
            providers_dict[provider_instance.key] = data
            
            status = data.status
            if status in ('critical', 'unavailable'):
                has_critical = True
            elif status == 'warning':
                has_warning = True
        except Exception as e:
            fallback = ProviderResult(
                status="unavailable",
                health_score=0,
                title=f"Provider Instance: {provider_class.__name__}",
                summary="Failed to instantiate provider.",
                checks=[CheckResult(name="Init", status="critical", message=str(e))],
                metrics={},
                technical_details=str(e)
            )
            providers_dict[f"failed_{provider_class.__name__}"] = fallback
            has_critical = True

    # 2. Activity Feed (SSR Filtering & Pagination)
    query = request.GET.get('q', '')
    severity = request.GET.get('severity', '')
    
    events_qs = SystemEvent.objects.all()
    if query:
        events_qs = events_qs.filter(message__icontains=query)
    if severity and severity != 'all':
        events_qs = events_qs.filter(severity=severity)
        
    events = events_qs[:50]

    # 3. Quick Actions
    quick_actions = [
        QuickAction(title="Upload Workbook", icon="ti-upload", url="#", permission="admin"),
        QuickAction(title="Attendance", icon="ti-calendar", url="#", permission="admin"),
        QuickAction(title="BTPL", icon="ti-truck", url="#", permission="admin"),
        QuickAction(title="COF", icon="ti-file-certificate", url="#", permission="admin"),
        QuickAction(title="FTL", icon="ti-package", url="#", permission="admin"),
        QuickAction(title="Reports", icon="ti-chart-pie", url="#", permission="admin"),
    ]

    # 4. Diagnostics & Infrastructure Models
    provider_diagnostics = []
    for key, p in providers_dict.items():
        provider_diagnostics.append(ProviderDiagnostic(
            key=key,
            title=p.title,
            summary=p.summary,
            status=p.status,
            health_score=p.health_score,
            execution_duration="< 50ms", # placeholder for now until we add timing to BaseProvider
            checks=[{"name": c.name, "status": c.status, "message": c.message} for c in p.checks],
            last_updated=p.last_updated
        ))
        
    infra_data = {}
    if 'storage' in providers_dict:
        s_metrics = providers_dict['storage'].metrics
        data_arr = s_metrics.get('data', [1, 1])
        used, free = data_arr[0], data_arr[1]
        pct = int(used / (used + free) * 100) if (used + free) > 0 else 0
        infra_data['storage_percent'] = pct
        infra_data['storage_metrics'] = s_metrics
        infra_data['storage_status'] = providers_dict['storage'].status
        
    if 'database' in providers_dict:
        infra_data['database_status'] = providers_dict['database'].status
        infra_data['database_metrics'] = providers_dict['database'].metrics
        
    if 'backups' in providers_dict:
        infra_data['backup_status'] = providers_dict['backups'].status
        infra_data['backup_metrics'] = providers_dict['backups'].metrics

    if 'performance' in providers_dict:
        infra_data['performance_metrics'] = providers_dict['performance'].metrics
        
    if 'activity' in providers_dict:
        infra_data['activity_metrics'] = providers_dict['activity'].metrics

    kpi_metrics = {
        'enabled_accounts': providers_dict.get('business').metrics.get('Enabled Accounts', '--') if 'business' in providers_dict else '--',
        'avg_response': providers_dict.get('performance').metrics.get('Avg Latency', '--') if 'performance' in providers_dict else '--',
        'system_events': providers_dict.get('activity').metrics.get('Events (24h)', '--') if 'activity' in providers_dict else '--',
        'db_size': providers_dict.get('database').metrics.get('File Size', '--') if 'database' in providers_dict else '--',
    }

    # 5. Build ViewModel
    dashboard = OperationsDashboard(
        operational_score=InsightsService.calculate_operational_score(providers_dict, has_critical, has_warning),
        insights=InsightsService.generate_predictive_insights(providers_dict, has_critical),
        executive_summary=InsightsService.generate_executive_summary(providers_dict, has_critical),
        quick_actions=quick_actions,
        providers=provider_diagnostics,
        infrastructure=infra_data,
        business_modules={
            'attendance': providers_dict.get('attendance'),
            'btpl': providers_dict.get('btpl'),
            'cof': providers_dict.get('cof'),
            'ftl': providers_dict.get('ftl'),
            'salary': providers_dict.get('salary'),
            'business': providers_dict.get('business'),
        },
        kpi_metrics=kpi_metrics,
        events=events
    )

    context = {
        'dashboard': dashboard,
        'q': query,
        'severity': severity
    }
    return render(request, 'core/portal/operations_center.html', context)

