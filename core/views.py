from django.shortcuts import render
from django.http import HttpResponse
from .models import Pincode
from django.template import loader
import datetime
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
import os
from django.core.files.base import ContentFile
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from .forms import CofForm, WorkbookUploadForm
from . import cof

from .decorators import staff_required
from .models import ToolRun, ToolRunFile, CofWorkbook

def home(request):
    return render(request, 'core/home.html')

def services(request):
    return render(request, 'core/services.html')

def contact(request):
    return render(request, 'core/contact.html')

def about(request):
    return render(request, 'core/about.html')

def privacy(request):
    return render(request, 'core/privacy.html')

def sitemap(request):
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>http://ecofleetexpress.com/</loc>
    <lastmod>2026-06-07</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>http://ecofleetexpress.com/about/</loc>
    <lastmod>2026-06-07</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>http://ecofleetexpress.com/services/</loc>
    <lastmod>2026-06-07</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>http://ecofleetexpress.com/contact/</loc>
    <lastmod>2026-06-07</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>http://ecofleetexpress.com/privacy/</loc>
    <lastmod>2026-06-07</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>'''
    return HttpResponse(xml_content, content_type='application/xml')

def find_location(request):
    result = None
    pincode = request.GET.get('pincode', '').strip()

    if pincode:
        try:
            pin_obj = Pincode.objects.get(pin=pincode)
            result = {
                'found': True,
                'pin': pin_obj.pin,
                'city': pin_obj.city,
                'state': pin_obj.state,
                'location_type': pin_obj.location_type,
            }
        except Pincode.DoesNotExist:
            result = {'found': False}

    return render(request, 'core/find_location.html', {'result': result, 'pincode': pincode})

# ─────────────────────────────────────────────
# EMPLOYEE PORTAL
# ─────────────────────────────────────────────
def portal_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard')

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            if not user.is_staff:
                messages.error(request, "This account isn't authorised for the employee portal.")
            else:
                auth_login(request, user)
                nxt = request.POST.get('next') or request.GET.get('next')
                if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
                    return redirect(nxt)
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'core/portal/login.html', {'form': form})


def portal_logout(request):
    auth_logout(request)
    messages.success(request, "You've been logged out.")
    return redirect('portal_login')


@staff_required
def dashboard(request):
    User = get_user_model()
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # ── Pincode coverage ──
    total_pincodes = Pincode.objects.count()
    oda = Pincode.objects.filter(location_type__iexact='ODA').count()
    non_oda = total_pincodes - oda

    # ── Operational counts (light up as the tools come online) ──
    cofs_month = ToolRun.objects.filter(
        tool=ToolRun.TOOL_COF, status=ToolRun.STATUS_SUCCESS,
        created_at__gte=month_start).count()
    reports_month = ToolRun.objects.filter(
        tool__in=[ToolRun.TOOL_MORNING, ToolRun.TOOL_PENDENCY],
        status=ToolRun.STATUS_SUCCESS, created_at__gte=month_start).count()
    total_runs = ToolRun.objects.count()
    team_members = User.objects.filter(is_staff=True, is_active=True).count()

    # ── Top states by coverage ──
    top_states = list(
        Pincode.objects.values('state')
        .annotate(c=Count('id')).order_by('-c')[:8])
    state_labels = [s['state'] or 'Unknown' for s in top_states]
    state_data = [s['c'] for s in top_states]

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
                    usage.get(ToolRun.TOOL_PENDENCY, 0)]

    chart_data = {
        'coverage': {'oda': oda, 'non_oda': non_oda},
        'states': {'labels': state_labels, 'data': state_data},
        'activity': {'labels': activity_labels, 'data': activity_data},
        'tools': {'labels': ['COF', 'Morning Report', 'Pendency'], 'data': tool_counts},
    }

    ctx = {
        'active': 'dashboard',
        'today': datetime.date.today().strftime('%A, %d %B %Y'),
        'total_pincodes': total_pincodes,
        'oda': oda,
        'non_oda': non_oda,
        'states_served': Pincode.objects.values('state').distinct().count(),
        'cofs_month': cofs_month,
        'reports_month': reports_month,
        'total_runs': total_runs,
        'team_members': team_members,
        'chart_data': chart_data,
        'recent_runs': ToolRun.objects.select_related('user')[:8],
    }
    return render(request, 'core/portal/dashboard.html', ctx)


# ── COF Generator (upload-once server-workbook model) ──
@staff_required
def cof_generator(request):
    wb_obj = CofWorkbook.active()
    if not wb_obj:
        return redirect('cof_workbook')

    wb_path = wb_obj.file.path

    try:
        preview = cof.get_next_cof_info(wb_path)
        preview_error = None
    except Exception as e:
        preview, preview_error = None, str(e)

    if request.method == 'POST':
        form = CofForm(request.POST)
        if form.is_valid():
            data = form.to_cof_data()
            try:
                result = cof.generate_cof(data, wb_path)
            except (cof.COFLockTimeout, cof.WorkbookInUse,
                    cof.WorkbookInvalid, cof.AssetMissing) as e:
                messages.error(request, str(e))
            except Exception as e:
                ToolRun.objects.create(
                    user=request.user, tool=ToolRun.TOOL_COF,
                    status=ToolRun.STATUS_FAILED,
                    reference=preview['cof_number'] if preview else '',
                    detail=f"Error: {e}")
                messages.error(request, f"Failed to generate COF: {e}")
            else:
                run = ToolRun.objects.create(
                    user=request.user, tool=ToolRun.TOOL_COF,
                    status=ToolRun.STATUS_SUCCESS, reference=result['cof_number'],
                    detail=f"Sheet: {result['sheet_name']} · Consignee: {data['consignee_name']}")
                ToolRunFile.objects.create(
                    run=run, label="COF document",
                    file=ContentFile(result['docx'].getvalue(), name=result['docx_name']))
                messages.success(request, f"{result['cof_number']} generated successfully.")
                return redirect('cof_success', pk=run.pk)
        else:
            messages.error(request, "Please fix the highlighted fields.")
    else:
        form = CofForm()

    return render(request, 'core/portal/cof_form.html', {
        'active': 'cof', 'form': form, 'preview': preview,
        'preview_error': preview_error, 'wb': wb_obj,
    })


@staff_required
def cof_workbook(request):
    """Upload / replace / remove the active tracking workbook."""
    wb_obj = CofWorkbook.active()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'remove' and wb_obj:
            wb_obj.is_active = False
            wb_obj.save(update_fields=['is_active'])
            messages.success(request, "Active workbook removed. Upload one to continue.")
            return redirect('cof_workbook')

        form = WorkbookUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.cleaned_data['workbook']
            new = CofWorkbook.objects.create(
                file=upload, original_name=upload.name,
                uploaded_by=request.user, is_active=False)
            try:
                cof.validate_workbook(new.file.path)
            except cof.WorkbookInvalid as e:
                new.file.delete(save=False)
                new.delete()
                messages.error(request, str(e))
                return redirect('cof_workbook')
            CofWorkbook.objects.filter(is_active=True).update(is_active=False)
            new.is_active = True
            new.save(update_fields=['is_active'])
            messages.success(request, f"“{upload.name}” is now the active tracking workbook.")
            return redirect('cof_generator')
        else:
            messages.error(request, "Please choose a valid .xlsx file.")
    else:
        form = WorkbookUploadForm()

    info = None
    if wb_obj:
        try:
            info = cof.get_next_cof_info(wb_obj.file.path)
        except Exception:
            info = None
    return render(request, 'core/portal/cof_workbook.html', {
        'active': 'cof', 'form': form, 'wb': wb_obj, 'info': info,
    })


@staff_required
def cof_success(request, pk):
    run = get_object_or_404(ToolRun.objects.prefetch_related('files'),
                            pk=pk, tool=ToolRun.TOOL_COF, status=ToolRun.STATUS_SUCCESS)
    return render(request, 'core/portal/cof_success.html', {'active': 'cof', 'run': run})


@staff_required
def cof_history(request):
    wb_obj = CofWorkbook.active()
    q = request.GET.get('q', '').strip()
    rows = []
    if wb_obj:
        rows = list(reversed(cof.load_history(wb_obj.file.path)))
        if q:
            ql = q.lower()
            rows = [r for r in rows if any(ql in str(v).lower() for v in r.values())]
    display = [{
        'num': r.get('#', ''), 'lr': r.get('LR Number', ''),
        'invoice': r.get('Invoice Number', ''), 'dealer': r.get('Dealer', ''),
        'state': r.get('State', ''), 'claim': r.get('Claim Amount', ''),
        'status': r.get('Status Delhivery', ''), 'cof_date': r.get('COF Date', ''),
        'optlog': r.get('Status Optlog', ''),
    } for r in rows]
    return render(request, 'core/portal/cof_history.html', {
        'active': 'cof', 'rows': display, 'q': q, 'total': len(display), 'wb': wb_obj,
    })


@staff_required
def cof_workbook_download(request):
    wb_obj = CofWorkbook.active()
    if not wb_obj:
        raise Http404("No active workbook.")
    return FileResponse(wb_obj.file.open('rb'), as_attachment=True,
                        filename=wb_obj.original_name)


@staff_required
def download_file(request, file_id):
    f = get_object_or_404(ToolRunFile, pk=file_id)
    if not f.file:
        raise Http404("File not available.")
    return FileResponse(f.file.open('rb'), as_attachment=True,
                        filename=os.path.basename(f.file.name))


@staff_required
def morning_report(request):
    return render(request, 'core/portal/coming_soon.html',
                {'active': 'morning', 'heading': 'Morning Report', 'phase': 'Phase 4'})


@staff_required
def pendency_report(request):
    return render(request, 'core/portal/coming_soon.html',
                {'active': 'pendency', 'heading': 'Pendency Report', 'phase': 'Phase 5'})