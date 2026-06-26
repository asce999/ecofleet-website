import os
from django.conf import settings
from django.http import JsonResponse
from django.db import connection
from django.db.utils import OperationalError
from core.models import AttendanceWorkbook
from django.utils import timezone
from core.decorators import staff_required

def health_check(request):
    status = {
        'status': 'ok',
        'components': {
            'django': 'ok',
            'database': 'unknown',
            'media': 'unknown',
            'static': 'unknown',
            'attendance_workbook': 'unknown'
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

    # 4. Attendance Workbook
    try:
        if AttendanceWorkbook.objects.filter(is_active=True).exists():
            status['components']['attendance_workbook'] = 'ok'
        else:
            status['components']['attendance_workbook'] = 'missing'
    except Exception:
        status['components']['attendance_workbook'] = 'error'

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
from core.operations.providers.base import BaseProvider

@staff_required
def operations_center(request):
    """
    Operations Center Dashboard.
    Aggregates data from all providers in core.operations.providers and fetches recent events.
    """
    providers_data = []
    has_critical = False
    has_warning = False
    total_health = 0
    provider_count = 0
    
    # Dynamically discover and instantiate all concrete providers
    import core.operations.providers as provider_package
    
    for _, module_name, _ in pkgutil.iter_modules(provider_package.__path__):
        if module_name == 'base':
            continue
            
        full_module_name = f"{provider_package.__name__}.{module_name}"
        try:
            module = importlib.import_module(full_module_name)
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseProvider) and obj is not BaseProvider:
                    provider_instance = obj(request)
                    data = provider_instance.get_data()
                    providers_data.append(data)
                    
                    status = data.get('status')
                    if status == 'critical' or status == 'unavailable':
                        has_critical = True
                    elif status == 'warning':
                        has_warning = True
                        
                    total_health += data.get('health_score', 0)
                    provider_count += 1
        except Exception as e:
            # If the module entirely fails to load, create a placeholder critical provider
            providers_data.append({
                "status": "unavailable",
                "health_score": 0,
                "title": f"Provider Module: {module_name}",
                "summary": f"Failed to load provider module.",
                "checks": [{"name": "Load", "status": "critical", "message": str(e)}],
                "metrics": {},
                "warnings": [],
                "errors": [],
                "technical_details": str(e),
                "last_updated": timezone.now()
            })
            has_critical = True
            provider_count += 1

    overall_health_score = int(total_health / provider_count) if provider_count > 0 else 0

    # Get recent system events
    events = SystemEvent.objects.all()[:20]

    # Map providers by a normalized key for specific component placement
    providers_dict = {}
    for p in providers_data:
        title = p.get('title', '').lower()
        # NOTE: check 'activity' before 'system' — ActivityProvider's title is
        # "System Activity", which would otherwise be swallowed by the 'system' branch.
        if 'activity' in title: providers_dict['activity'] = p
        elif 'system' in title: providers_dict['system'] = p
        elif 'database' in title: providers_dict['database'] = p
        elif 'backups' in title: providers_dict['backups'] = p
        elif 'storage' in title: providers_dict['storage'] = p
        elif 'attendance' in title: providers_dict['attendance'] = p
        elif 'salary' in title: providers_dict['salary'] = p
        elif 'btpl' in title: providers_dict['btpl'] = p
        elif 'ftl' in title: providers_dict['ftl'] = p
        elif 'cof' in title: providers_dict['cof'] = p
        elif 'security' in title: providers_dict['security'] = p
        elif 'performance' in title: providers_dict['performance'] = p
        elif 'business' in title: providers_dict['business'] = p

    # Gather critical messages and construct Score Breakdown
    critical_messages = []
    warning_messages = []
    
    # Categorize providers for Breakdown
    categories = {
        'Infrastructure': ['system', 'database'],
        'Business Modules': ['attendance', 'salary', 'btpl', 'ftl', 'cof', 'business'],
        'Security': ['security'],
        'Performance': ['performance', 'activity'],
        'Storage & Backups': ['storage', 'backups']
    }
    
    score_breakdown = {}
    for cat_name, keys in categories.items():
        cat_total = 0
        cat_max = 0
        for key in keys:
            if key in providers_dict:
                cat_total += providers_dict[key].get('health_score', 0)
                cat_max += 100
        if cat_max > 0:
            # Calculate how much this category contributed to the overall score
            # A category adds (cat_total / (provider_count * 100)) * 100 to the 100-point total
            contribution = (cat_total / (provider_count * 100)) * 100 if provider_count > 0 else 0
            # Also calculate how many points it lost
            max_contribution = (cat_max / (provider_count * 100)) * 100 if provider_count > 0 else 0
            lost = max_contribution - contribution
            score_breakdown[cat_name] = {
                'earned': round(contribution),
                'lost': round(lost),
                'status': 'healthy' if lost == 0 else ('warning' if lost < 5 else 'critical')
            }

    if has_critical or has_warning:
        for p in providers_data:
            if p.get('status') == 'critical':
                for check in p.get('checks', []):
                    if check.get('status') == 'critical':
                        critical_messages.append(f"{p.get('title', 'Unknown')}: {check.get('message', 'Failed')}")
                if not p.get('checks'):
                    critical_messages.append(f"{p.get('title', 'Unknown')} is critical")
            elif p.get('status') == 'warning':
                for check in p.get('checks', []):
                    if check.get('status') == 'warning':
                        warning_messages.append(f"{p.get('title', 'Unknown')}: {check.get('message', 'Needs Attention')}")

    # Generate predictive insights
    insights = []
    
    # 1. Database Insight (Needs historical data for projections)
    db_data = providers_dict.get('database', {})
    db_size = db_data.get('metrics', {}).get('File Size', '0 MB')
    try:
        size_val = float(db_size.split()[0])
        if size_val > 500:
            insights.append({"type": "warning", "icon": "ti-database", "message": f"Database size is {size_val:.1f}MB. Optimization recommended."})
        else:
            # We don't have historical growth data, so we cannot project when it reaches 80%
            insights.append({"type": "info", "icon": "ti-chart-line", "message": "Collecting operational history for storage projections."})
    except:
        pass
        
    # 2. Performance insight
    perf_data = providers_dict.get('performance', {})
    latency = perf_data.get('metrics', {}).get('Avg Latency', '0 ms')
    try:
        lat_val = float(latency.split()[0])
        if lat_val > 500:
            insights.append({"type": "warning", "icon": "ti-bolt", "message": f"Performance degrading. Average latency is {lat_val:.0f}ms."})
        elif lat_val > 0:
            insights.append({"type": "info", "icon": "ti-chart-line", "message": "Collecting operational history for performance trends."})
    except:
        pass
        
    # 3. Backups insight
    backup_data = providers_dict.get('backups', {})
    last_backup = backup_data.get('metrics', {}).get('Latest Backup', 'N/A')
    if last_backup == 'N/A':
        insights.append({"type": "danger", "icon": "ti-shield", "message": "No backups found."})
    else:
        insights.append({"type": "success", "icon": "ti-shield", "message": "Backup freshness excellent."})
        
    # 4. Criticals insight
    if not has_critical:
        insights.append({"type": "success", "icon": "ti-check", "message": "No critical system failures."})
        
    # Generate Executive Summary
    executive_summary = []
    
    # Reports
    biz_data = providers_dict.get('business', {})
    reports_today = biz_data.get('metrics', {}).get('Reports Today')
    if reports_today:
        executive_summary.append({"icon": "check", "color": "success", "text": f"{reports_today} reports generated today"})
    
    # Attendance
    att_data = providers_dict.get('attendance', {})
    att_jobs = att_data.get('metrics', {}).get('Jobs Today')
    if att_jobs:
        executive_summary.append({"icon": "check", "color": "success", "text": f"{att_jobs} attendance uploads completed"})
        
    # Statuses
    if not has_critical:
        executive_summary.append({"icon": "check", "color": "success", "text": "All business modules operational"})
    if has_critical:
        executive_summary.append({"icon": "alert-triangle", "color": "danger", "text": "Critical failures detected in infrastructure"})
        
    if last_backup != 'N/A':
        executive_summary.append({"icon": "check", "color": "success", "text": "Database backup completed successfully"})
    else:
        executive_summary.append({"icon": "alert-triangle", "color": "warning", "text": "No recent backups found"})
        
    if latency != '0 ms':
        executive_summary.append({"icon": "check", "color": "success", "text": f"Platform latency stable at {latency}"})

    context = {
        'providers': providers_data,
        'providers_dict': providers_dict,
        'has_critical': has_critical,
        'has_warning': has_warning,
        'overall_health_score': overall_health_score,
        'critical_messages': critical_messages,
        'warning_messages': warning_messages,
        'score_breakdown': score_breakdown,
        'executive_summary': executive_summary,
        'insights': insights,
        'events': events,
    }
    return render(request, 'core/portal/operations_center.html', context)
