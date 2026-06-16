from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import FileResponse
from core.models import ToolRun, ToolRunFile
from core.forms import PendencyForm
from core.decorators import staff_required, tool_permission_required
from django.core.files.base import ContentFile
from core import pendency as pendency_logic
import io
import pandas as pd
import datetime


@staff_required
@tool_permission_required('pendency')
def pendency_report(request):
    latest_run = ToolRun.objects.filter(tool=ToolRun.TOOL_PENDENCY, status=ToolRun.STATUS_SUCCESS).first()
    latest_file = latest_run.files.last() if latest_run else None
    
    preview = None
    all_lrs = {}
    if latest_file:
        preview = _pendency_preview(latest_file)
        all_lrs = _get_all_lrs_from_workbook(latest_file)

    if request.method == 'POST':
        form = PendencyForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                buf, summary = pendency_logic.generate(
                    cd['file_2w'], cd['file_cv'],
                    cd['file_2w'].name, cd['file_cv'].name,
                    cd.get('min_delay_days') or 1,
                    cd.get('all_in_transit') or False)
            except pendency_logic.ReportError as e:
                messages.error(request, str(e))
            except Exception as e:
                ToolRun.objects.create(
                    user=request.user, tool=ToolRun.TOOL_PENDENCY,
                    status=ToolRun.STATUS_FAILED, detail=f"Error: {e}")
                messages.error(request, f"Failed to generate report: {e}")
            else:
                fname = f"{cd['report_name']}.xlsx"
                run = ToolRun.objects.create(
                    user=request.user, tool=ToolRun.TOOL_PENDENCY,
                    status=ToolRun.STATUS_SUCCESS, reference=cd['report_name'],
                    detail=(f"2W: {summary['count_2w']} · CV: {summary['count_cv']} "
                            f"shipments · Month: {summary['month']}"))
                ToolRunFile.objects.create(
                    run=run, label="Pendency report", download_name=fname,
                    file=ContentFile(buf.getvalue(), name=fname))
                messages.success(request, "Pendency report generated.")
                return redirect('tool_result', pk=run.pk)
        else:
            messages.error(request, "Please fix the highlighted fields.")
    else:
        form = PendencyForm()
    
    return render(request, 'core/portal/pendency_form.html', {
        'active': 'pendency',
        'form': form,
        'latest_run': latest_run,
        'current': latest_file,
        'preview': preview,
        'all_lrs': all_lrs,
    })


def _read_file_bytes(tool_file):
    """Read a ToolRunFile's bytes (open/close safely)."""
    f = tool_file.file
    f.open('rb')
    try:
        return f.read()
    finally:
        f.close()


def _pendency_preview(tool_file, max_rows=15):
    """Build a small per-sheet preview of a pendency workbook for the UI."""
    try:
        data = _read_file_bytes(tool_file)
        xls = pd.ExcelFile(io.BytesIO(data))
    except Exception:
        return []
    sheets = []
    for name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=name, nrows=max_rows).fillna("")
        except Exception:
            continue
        sheets.append({
            'name': name,
            'columns': [str(c) for c in df.columns],
            'rows': df.astype(str).values.tolist(),
        })
    return sheets


def _get_all_lrs_from_workbook(tool_file):
    """Get all LR numbers from the 2W and CV sheets as a dict: {sheet_name: [lr1, lr2, ...]}."""
    try:
        data = _read_file_bytes(tool_file)
        xls = pd.ExcelFile(io.BytesIO(data))
    except Exception:
        return {}
    
    result = {}
    for name in xls.sheet_names:
        if name in ("2W", "CV"):
            try:
                df = pd.read_excel(xls, sheet_name=name)
                df.columns = [str(c).strip().lower() for c in df.columns]
                lr_col = next((c for c in df.columns if c in ("lr no.", "lr no", "lr number", "lrn")), None)
                if lr_col:
                    lrs = df[lr_col].dropna().astype(str).str.strip().str.replace(r'\.0$', '', regex=True).tolist()
                    result[name] = lrs
            except Exception:
                continue
    return result


@staff_required
@tool_permission_required('pendency')
def pendency_observations(request, pk):
    """Override / fill the Observation column of an existing pendency report by
    uploading one or more observation CSVs, matched strictly by LR Number."""
    run = get_object_or_404(
        ToolRun.objects.prefetch_related('files'),
        pk=pk, tool=ToolRun.TOOL_PENDENCY, status=ToolRun.STATUS_SUCCESS)
    current = run.files.last()  # newest report (original, or a prior override)
    if not current or not current.file:
        raise Http404("No pendency report file to enrich.")

    if request.method == 'POST':
        obs_files = request.FILES.getlist('observation_files')
        if not obs_files:
            messages.error(request, "Upload at least one observation CSV.")
        elif any(not f.name.lower().endswith('.csv') for f in obs_files):
            messages.error(request, "Observation files must be .csv.")
        else:
            try:
                obs_map, load_stats = pendency_logic.load_observation_csvs(obs_files)
                report_bytes = _read_file_bytes(current)
                buf, apply_stats = pendency_logic.apply_observations(report_bytes, obs_map)
            except pendency_logic.ReportError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Failed to apply observations: {e}")
            else:
                fname = f"{run.reference or 'pendency'}_with_observations.xlsx"
                ToolRunFile.objects.create(
                    run=run, label="Pendency report (observations updated)",
                    download_name=fname,
                    file=ContentFile(buf.getvalue(), name=fname))
                extra = (f"Observations applied: {apply_stats['matched']} matched "
                         f"from {load_stats['unique']} CSV record(s)")
                if apply_stats['unmatched_count']:
                    extra += f" · {apply_stats['unmatched_count']} CSV LR(s) unmatched"
                run.detail = f"{run.detail} · {extra}"
                run.save(update_fields=['detail'])
                messages.success(
                    request, f"{apply_stats['matched']} observation(s) applied by exact LR match.")
                if apply_stats['unmatched_count']:
                    sample = ", ".join(apply_stats['unmatched_obs'][:10])
                    more = "…" if apply_stats['unmatched_count'] > 10 else ""
                    messages.warning(
                        request, f"{apply_stats['unmatched_count']} LR(s) from the CSV(s) "
                                 f"matched no report row: {sample}{more}")
                return redirect('tool_result', pk=run.pk)

    return render(request, 'core/portal/pendency_observations.html', {
        'active': 'pendency', 'run': run, 'current': current,
        'preview': _pendency_preview(current),
        'all_lrs': _get_all_lrs_from_workbook(current),
    })


