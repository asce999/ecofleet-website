from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404
from core.models import ToolRun, CofWorkbook
from core.forms import CofForm, WorkbookUploadForm
from core.decorators import staff_required, tool_permission_required
from core.views.common import download_file
from core import cof as cof_logic
import io
import os
from django.conf import settings


@staff_required
@tool_permission_required('cof')
def cof_generator(request):
    wb_obj = CofWorkbook.active()
    if not wb_obj:
        return redirect('cof_workbook')

    wb_path = wb_obj.file.path

    try:
        preview = cof_logic.get_next_cof_info(wb_path)
        preview_error = None
    except Exception as e:
        preview, preview_error = None, str(e)

    if request.method == 'POST':
        form = CofForm(request.POST)
        if form.is_valid():
            data = form.to_cof_data()
            try:
                result = cof_logic.generate_cof(data, wb_path)
            except (cof_logic.COFLockTimeout, cof_logic.WorkbookInUse,
                    cof_logic.WorkbookInvalid, cof_logic.AssetMissing) as e:
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
                    run=run, label="COF document", download_name=result['docx_name'],
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
@tool_permission_required('cof')
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
                cof_logic.validate_workbook(new.file.path)
            except cof_logic.WorkbookInvalid as e:
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
            info = cof_logic.get_next_cof_info(wb_obj.file.path)
        except Exception:
            info = None
    return render(request, 'core/portal/cof_workbook.html', {
        'active': 'cof', 'form': form, 'wb': wb_obj, 'info': info,
    })


@staff_required
@tool_permission_required('cof')
def cof_success(request, pk):
    run = get_object_or_404(ToolRun.objects.prefetch_related('files'),
                            pk=pk, tool=ToolRun.TOOL_COF, status=ToolRun.STATUS_SUCCESS)
    return render(request, 'core/portal/cof_success.html', {'active': 'cof', 'run': run})


@staff_required
@tool_permission_required('cof')
def cof_history(request):
    wb_obj = CofWorkbook.active()
    q = request.GET.get('q', '').strip()
    rows = []
    if wb_obj:
        rows = list(reversed(cof_logic.load_history(wb_obj.file.path)))
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
@tool_permission_required('cof')
def cof_workbook_download(request):
    wb_obj = CofWorkbook.active()
    if not wb_obj:
        raise Http404("No active workbook.")
    return FileResponse(wb_obj.file.open('rb'), as_attachment=True,
                        filename=wb_obj.original_name)


