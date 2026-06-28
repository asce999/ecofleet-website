from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Q  # required for pincode_dashboard_stats cache
from django.db.models.functions import TruncDate
from core.models import Pincode, ToolRun, ToolRunFile
from core.decorators import staff_required, director_required
from core.views.ftl import get_active_ftl_workbook
from django.core.cache import cache
from core import ftl as ftl_logic
import datetime
import os
from django.contrib import messages


@staff_required
def dashboard(request):
    User = get_user_model()
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # ── Pincode coverage ──
    pincode_stats = cache.get('pincode_dashboard_stats')
    if not pincode_stats:
        total_pincodes = Pincode.objects.count()
        oda = Pincode.objects.filter(location_type__iexact='ODA').count()
        non_oda = total_pincodes - oda
        states_served = Pincode.objects.values('state').distinct().count()

        top_states = list(
            Pincode.objects.values('state')
            .annotate(c=Count('id')).order_by('-c')[:8])
        state_labels = [s['state'] or 'Unknown' for s in top_states]
        state_data = [s['c'] for s in top_states]
        
        pincode_stats = {
            'total_pincodes': total_pincodes,
            'oda': oda,
            'non_oda': non_oda,
            'states_served': states_served,
            'state_labels': state_labels,
            'state_data': state_data,
        }
        cache.set('pincode_dashboard_stats', pincode_stats, 86400)
    
    total_pincodes = pincode_stats['total_pincodes']
    oda = pincode_stats['oda']
    non_oda = pincode_stats['non_oda']
    state_labels = pincode_stats['state_labels']
    state_data = pincode_stats['state_data']
    states_served = pincode_stats['states_served']

    # ── Operational counts (light up as the tools come online) ──
    cofs_month = ToolRun.objects.filter(
        tool=ToolRun.TOOL_COF, status=ToolRun.STATUS_SUCCESS,
        created_at__gte=month_start).count()
    reports_month = ToolRun.objects.filter(
        tool__in=[ToolRun.TOOL_MORNING, ToolRun.TOOL_PENDENCY, ToolRun.TOOL_PREV_MONTH],
        status=ToolRun.STATUS_SUCCESS, created_at__gte=month_start).count()
    total_runs = ToolRun.objects.count()
    team_members = User.objects.filter(is_staff=True, is_active=True).count()

    # ── Tool activity, last 14 days ──
    since = (now - datetime.timedelta(days=13)).date()
    by_day = {
        r['d']: r['c'] for r in
        ToolRun.objects.filter(created_at__date__gte=since)
        .annotate(d=TruncDate('created_at')).values('d')
        .annotate(c=Count('id'))
    }
    activity_labels, activity_data = [], []
    for i in range(13, -1, -1):
        day = (now - datetime.timedelta(days=i)).date()
        activity_labels.append(day.strftime('%d %b'))
        activity_data.append(by_day.get(day, 0))

    # ── Tool usage breakdown ──
    usage = {r['tool']: r['c'] for r in
            ToolRun.objects.values('tool').annotate(c=Count('id'))}
    tool_counts = [usage.get(ToolRun.TOOL_COF, 0),
                    usage.get(ToolRun.TOOL_MORNING, 0),
                    usage.get(ToolRun.TOOL_PENDENCY, 0),
                    usage.get(ToolRun.TOOL_PREV_MONTH, 0)]

    chart_data = {
        'coverage': {'oda': oda, 'non_oda': non_oda},
        'states': {'labels': state_labels, 'data': state_data},
        'activity': {'labels': activity_labels, 'data': activity_data},
        'tools': {'labels': ['COF', 'Morning Report', 'Pendency', 'Previous Month Update'], 'data': tool_counts},
    }

    # ── FTL metrics ──
    ftl_wb_obj, ftl_file_path, ftl_sheet_name = get_active_ftl_workbook()
    ftl_total, ftl_delivered, ftl_in_transit, ftl_vendors = ftl_logic.get_cached_ftl_metrics(
        ftl_wb_obj, ftl_file_path, ftl_sheet_name
    )

    ctx = {
        'active': 'dashboard',
        'today': datetime.date.today().strftime('%A, %d %B %Y'),
        'total_pincodes': total_pincodes,
        'oda': oda,
        'non_oda': non_oda,
        'states_served': states_served,
        'cofs_month': cofs_month,
        'reports_month': reports_month,
        'total_runs': total_runs,
        'team_members': team_members,
        'chart_data': chart_data,
        'recent_runs': ToolRun.objects.select_related('user')[:8],
        'ftl_total': ftl_total,
        'ftl_delivered': ftl_delivered,
        'ftl_in_transit': ftl_in_transit,
        'ftl_vendors': ftl_vendors,
    }
    return render(request, 'core/portal/dashboard.html', ctx)


@staff_required
@director_required
def portal_users(request):
    from django.contrib.auth.models import User
    from core.models import UserProfile

    users = User.objects.filter(is_staff=True).order_by('username')
    for u in users:
        UserProfile.objects.get_or_create(user=u)

    if request.method == 'POST':
        for u in users:
            if u == request.user:
                continue

            profile = u.profile
            role = request.POST.get(f"role_{u.id}", "Employee")
            profile.role = role

            profile.can_use_cof = f"cof_{u.id}" in request.POST
            profile.can_use_morning = f"morning_{u.id}" in request.POST
            profile.can_use_pendency = f"pendency_{u.id}" in request.POST
            profile.can_use_prev_month = f"prev_month_{u.id}" in request.POST
            profile.can_use_btpl = f"btpl_{u.id}" in request.POST
            profile.can_use_attendance = f"attendance_{u.id}" in request.POST
            profile.can_use_ftl = f"ftl_{u.id}" in request.POST
            profile.save()

        messages.success(request, "User roles and permissions updated successfully.")
        return redirect('portal_users')

    profiles = [u.profile for u in users]
    return render(request, 'core/portal/users.html', {
        'active': 'users',
        'profiles': profiles,
    })


