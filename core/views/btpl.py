from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404, JsonResponse
from core.models import BtplWorkbook
from core.forms import BtplShipmentForm, BtplWorkbookUploadForm
from core.decorators import staff_required, tool_permission_required, tool_permission_required
from core import btpl as btpl_logic
import os
import json
import datetime
from core.models import ToolRun
from django.contrib import messages
from core.utils.parsing import safe_int
from core.workbook.locking import workbook_lock
import uuid
from django.conf import settings
import logging

logger = logging.getLogger(__name__)



def get_active_btpl_workbook():
    # If there are BtplWorkbook records but no active one, it means sheet was removed entirely!
    wb_count = BtplWorkbook.objects.count()
    if wb_count > 0:
        wb_obj = BtplWorkbook.active()
        if not wb_obj:
            return None, None, None
        return wb_obj, wb_obj.file.path, wb_obj.active_sheet
    else:
        # Initial fresh state: fall back to default
        file_path = os.path.join(settings.BASE_DIR, 'efe_data', 'BTPL_Shipments.xlsx')
        sheet_name = 'JUN 26'
        return None, file_path, sheet_name


@staff_required
@tool_permission_required('btpl')
@never_cache
def btpl_sheet(request):
    from django.urls import reverse
    wb_obj, file_path, sheet_name = get_active_btpl_workbook()
    
    if not file_path:
        return render(request, 'core/portal/btpl_form.html', {
            'active': 'btpl',
            'no_sheet': True,
        })

    page = safe_int(request.GET.get('page', 1), 1)
    page_data = btpl_logic.get_btpl_page_data(
        file_path, sheet_name=sheet_name, page=page, page_size=20
    )

    if page_data is None:
        return render(request, 'core/portal/btpl_form.html', {
            'active': 'btpl',
            'no_sheet': True,
        })

    totals_row = page_data['totals_row']
    next_row = page_data['next_row']

    context = {
        'active': 'btpl',
        'preview': page_data['preview'],
        'next_row': next_row,
        'totals_row': totals_row,
        'max_shipment_row': totals_row - 1,
        'sheet_name': sheet_name,
        'wb': wb_obj,
    }
    return render(request, 'core/portal/btpl_form.html', context)


@staff_required
@tool_permission_required('btpl')
@never_cache
def btpl_api(request):
    """JSON API endpoint for AJAX BTPL operations."""
    import json
    from django.http import JsonResponse

    wb_obj, file_path, sheet_name = get_active_btpl_workbook()
    if not file_path:
        return JsonResponse({'error': 'No active workbook'}, status=404)

    action = request.GET.get('action') or request.POST.get('action', '')

    # GET: fetch row data for editing
    if action == 'get_row':
        row_num = safe_int(request.GET.get('row', 0), 0)
        if row_num < 2:
            return JsonResponse({'error': 'Invalid row'}, status=400)
        row_data = btpl_logic.get_btpl_row_values(file_path, row_num, sheet_name=sheet_name)
        # Convert dates to strings for JSON
        for key in ['pickup_date', 'delivered_on']:
            val = row_data.get(key)
            if isinstance(val, (datetime.datetime, datetime.date)):
                row_data[key] = val.strftime('%Y-%m-%d')
        return JsonResponse({'row_data': row_data})

    # GET: paginated preview
    if action == 'preview':
        page = safe_int(request.GET.get('page', 1), 1)
        preview = btpl_logic.get_btpl_preview(file_path, sheet_name=sheet_name, page=page, page_size=20)
        return JsonResponse({'preview': preview})

    # POST: save row
    if action == 'save' and request.method == 'POST':
        form = BtplShipmentForm(request.POST)
        if form.is_valid():
            row_data = form.cleaned_data
            target_row = row_data['row_num']
            try:
                with workbook_lock(file_path):
                    btpl_logic.add_btpl_shipment(file_path, row_data, sheet_name=sheet_name)
                run = ToolRun.objects.create(
                    user=request.user,
                    tool=ToolRun.TOOL_BTPL,
                    status=ToolRun.STATUS_SUCCESS,
                    reference=f"LR: {row_data.get('lr_number') or ''}",
                    detail=f"Row: {target_row} · Sheet: {sheet_name} · Consignee: {row_data.get('name') or ''}"
                )
                return JsonResponse({'success': True, 'run_id': run.pk, 'row': target_row})
            except Exception as e:
                logger.error(f"Error generating BTPL row {target_row}: {e}")
                ToolRun.objects.create(
                    user=request.user,
                    tool=ToolRun.TOOL_BTPL,
                    status=ToolRun.STATUS_FAILED,
                    detail=f"Error writing row {target_row}: {e}"
                )
                return JsonResponse({'error': str(e)}, status=500)
        else:
            errors = {k: v[0] for k, v in form.errors.items()}
            logger.warning(f"Workbook validation failure during BTPL processing by '{request.user.username}': {errors}")
            return JsonResponse({'error': 'Validation failed', 'field_errors': errors}, status=400)

    # POST: delete row
    if action == 'delete' and request.method == 'POST':
        row_num = safe_int(request.POST.get('row', 0), 0)
        # Get totals_row to validate
        page_data = btpl_logic.get_btpl_page_data(file_path, sheet_name=sheet_name, page=1, page_size=1)
        totals_row = page_data['totals_row'] if page_data else 64
        if row_num < 2 or row_num >= totals_row:
            return JsonResponse({'error': 'Invalid row number'}, status=400)
        try:
            with workbook_lock(file_path):
                btpl_logic.clear_btpl_row(file_path, row_num, sheet_name=sheet_name)
            ToolRun.objects.create(
                user=request.user,
                tool=ToolRun.TOOL_BTPL,
                status=ToolRun.STATUS_SUCCESS,
                reference=f"Clear Row: {row_num}",
                detail=f"Cleared all shipment details in Row {row_num} on sheet {sheet_name}"
            )
            return JsonResponse({'success': True, 'row': row_num})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # GET: next available row
    if action == 'next_row':
        next_row = btpl_logic.find_next_btpl_row(file_path, sheet_name=sheet_name)
        return JsonResponse({'next_row': next_row})

    return JsonResponse({'error': 'Unknown action'}, status=400)


@staff_required
@tool_permission_required('btpl')
def btpl_download(request):
    from core.services.workbook_manager import WorkbookManager
    wb_obj, file_path, sheet_name = get_active_btpl_workbook()
    
    stream = WorkbookManager.get_file_stream(wb_obj, 'BTPL_Shipments.xlsx')
    if not stream:
        raise Http404("BTPL Shipments file not found.")
    
    filename = wb_obj.original_name if wb_obj else "BTPL_Shipments.xlsx"
    logger.info(f"Report downloaded: BTPL Shipments '{filename}' by user '{request.user.username}'")
    response = FileResponse(stream, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@staff_required
@tool_permission_required('btpl')
def btpl_settings(request):
    """Manage active BTPL shipment workbook and active sheet tab."""
    wb_obj, file_path, current_sheet_name = get_active_btpl_workbook()
    
    # Read sheets from Excel if file_path exists
    from core.services.sheet_parser import get_sheet_names
    sheets = get_sheet_names(file_path)
    if not sheets:
        sheets = ['JUN 26']
        
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'remove':
            BtplWorkbook.objects.filter(is_active=True).update(is_active=False)
            if BtplWorkbook.objects.count() == 0:
                BtplWorkbook.objects.create(
                    original_name='BTPL_Shipments.xlsx',
                    active_sheet='JUN 26',
                    uploaded_by=request.user,
                    is_active=False
                )
            logger.info(f"Workbook archived/removed: BTPL Tracker by user '{request.user.username}'")
            messages.success(request, "BTPL shipment sheet removed entirely. Portal is now in empty state.")
            return redirect('btpl_settings')
            
        elif action == 'load_default':
            from core.services.workbook_manager import WorkbookManager
            
            # Deactivate any existing
            BtplWorkbook.objects.filter(is_active=True).update(is_active=False)
            
            file_name = WorkbookManager.load_default_template('btpl', 'BTPL_Shipments.xlsx')
            
            wb_obj = BtplWorkbook.objects.create(
                original_name='BTPL_Shipments.xlsx',
                active_sheet='JUN 26',
                uploaded_by=request.user,
                is_active=True
            )
            wb_obj.file.name = file_name
            wb_obj.save(update_fields=['file'])
            
            logger.info(f"Workbook activated: Default BTPL Tracker loaded by user '{request.user.username}'")
            messages.success(request, "Default BTPL shipment workbook loaded successfully.")
            return redirect('btpl_settings')
            
        elif action == 'change_sheet':
            form = BtplWorkbookUploadForm(request.POST, sheets=sheets)
            if form.is_valid():
                sheet_sel = form.cleaned_data.get('active_sheet')
                if wb_obj:
                    wb_obj.active_sheet = sheet_sel
                    wb_obj.save(update_fields=['active_sheet'])
                else:
                    # Copy root file to media directory and register in database
                    from core.services.workbook_manager import WorkbookManager
                    file_name = WorkbookManager.load_default_template('btpl', 'BTPL_Shipments.xlsx')
                    
                    wb_obj = BtplWorkbook.objects.create(
                        original_name='BTPL_Shipments.xlsx',
                        active_sheet=sheet_sel,
                        uploaded_by=request.user,
                        is_active=True
                    )
                    wb_obj.file.name = file_name
                    wb_obj.save(update_fields=['file'])
                    
                messages.success(request, f"Active sheet tab changed to '{sheet_sel}'.")
                return redirect('btpl_sheet')
                
        elif action == 'upload':
            form = BtplWorkbookUploadForm(request.POST, request.FILES, sheets=sheets)
            if form.is_valid():
                upload = request.FILES.get('workbook')
                if upload:
                    original_name = upload.name
                    ext = os.path.splitext(original_name)[1]
                    upload.name = f"btpl_{uuid.uuid4().hex}{ext}"
                    # Create new workbook record
                    new_wb = BtplWorkbook.objects.create(
                        file=upload, original_name=original_name,
                        uploaded_by=request.user, is_active=False
                    )
                    
                    # Read sheets from the uploaded workbook to set default active sheet
                    from core.services.sheet_parser import get_sheet_names
                    if new_wb.file:
                        sheetnames = get_sheet_names(new_wb.file.path)
                        if sheetnames:
                            new_wb.active_sheet = sheetnames[0]
                            new_wb.save(update_fields=['active_sheet'])
                    
                    # Deactivate existing active workbook
                    BtplWorkbook.objects.filter(is_active=True).update(is_active=False)
                    new_wb.is_active = True
                    new_wb.save(update_fields=['is_active'])
                    
                    logger.info(f"Workbook uploaded: BTPL Tracker '{original_name}' by user '{request.user.username}'")
                    messages.success(request, f"Uploaded workbook '{original_name}' is now the active BTPL shipment workbook.")
                    return redirect('btpl_settings')
                else:
                    logger.warning(f"Workbook validation failure: No file provided for BTPL upload by user '{request.user.username}'")
                    messages.error(request, "Please choose a valid .xlsx file to upload.")
    else:
        form = BtplWorkbookUploadForm(initial={'active_sheet': current_sheet_name}, sheets=sheets)
        
    context = {
        'active': 'btpl',
        'form': form,
        'wb': wb_obj,
        'current_sheet': current_sheet_name,
        'sheets': sheets,
    }
    return render(request, 'core/portal/btpl_settings.html', context)


