from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect
from django.http import FileResponse, Http404
from core.models import FtlWorkbook
from core.forms import FtlShipmentForm, FtlWorkbookUploadForm
from core.decorators import staff_required, tool_permission_required
from core import ftl as ftl_logic
import os
from core.models import ToolRun
from django.contrib import messages
from django.conf import settings
import logging

logger = logging.getLogger(__name__)



def get_active_ftl_workbook():
    wb_count = FtlWorkbook.objects.count()
    if wb_count > 0:
        wb_obj = FtlWorkbook.active()
        if not wb_obj:
            return None, None, None
        return wb_obj, wb_obj.file.path, wb_obj.active_sheet
    else:
        file_path = os.path.join(settings.BASE_DIR, 'FTL_Shipment_Tracker.xlsx')
        sheet_name = 'Sheet1'
        return None, file_path, sheet_name


@staff_required
@tool_permission_required('ftl')
@never_cache
def ftl_sheet(request):
    from django.urls import reverse
    wb_obj, file_path, sheet_name = get_active_ftl_workbook()
    
    if not file_path or not os.path.exists(file_path):
        return render(request, 'core/portal/ftl_form.html', {
            'active': 'ftl',
            'no_sheet': True,
        })

    page = int(request.GET.get('page', 1))
    page_data = ftl_logic.get_ftl_page_data(
        file_path, sheet_name=sheet_name, page=page, page_size=20
    )

    if page_data is None:
        return render(request, 'core/portal/ftl_form.html', {
            'active': 'ftl',
            'no_sheet': True,
        })

    totals_row = page_data['totals_row']
    next_row = page_data['next_row']

    context = {
        'active': 'ftl',
        'preview': page_data['preview'],
        'next_row': next_row,
        'totals_row': totals_row,
        'max_shipment_row': totals_row - 1,
        'sheet_name': sheet_name,
        'wb': wb_obj,
    }
    return render(request, 'core/portal/ftl_form.html', context)


@staff_required
@tool_permission_required('ftl')
@never_cache
def ftl_api(request):
    """JSON API endpoint for AJAX FTL operations."""
    from django.http import JsonResponse

    wb_obj, file_path, sheet_name = get_active_ftl_workbook()
    if not file_path or not os.path.exists(file_path):
        return JsonResponse({'error': 'No active workbook'}, status=404)

    action = request.GET.get('action') or request.POST.get('action', '')

    # GET: fetch row data for editing
    if action == 'get_row':
        row_num = int(request.GET.get('row', 0))
        if row_num < 2:
            return JsonResponse({'error': 'Invalid row'}, status=400)
        row_data = ftl_logic.get_ftl_row_values(file_path, row_num, sheet_name=sheet_name)
        for key in ['booking_date', 'etd', 'delivery_date']:
            val = row_data.get(key)
            if isinstance(val, (datetime.datetime, datetime.date)):
                row_data[key] = val.strftime('%Y-%m-%d')
        return JsonResponse({'row_data': row_data})

    # GET: paginated preview
    if action == 'preview':
        page = int(request.GET.get('page', 1))
        preview = ftl_logic.get_ftl_preview(file_path, sheet_name=sheet_name, page=page, page_size=20)
        return JsonResponse({'preview': preview})

    # POST: save row
    if action == 'save' and request.method == 'POST':
        form = FtlShipmentForm(request.POST)
        if form.is_valid():
            row_data = form.cleaned_data
            target_row = row_data['row_num']
            try:
                ftl_logic.add_ftl_shipment(file_path, row_data, sheet_name=sheet_name)
                run = ToolRun.objects.create(
                    user=request.user,
                    tool=ToolRun.TOOL_FTL,
                    status=ToolRun.STATUS_SUCCESS,
                    reference=f"LR: {row_data.get('lr_number') or ''}",
                    detail=f"Row: {target_row} · Sheet: {sheet_name} · Vehicle: {row_data.get('vehicle_number') or ''}"
                )
                return JsonResponse({'success': True, 'run_id': run.pk, 'row': target_row})
            except Exception as e:
                logger.error(f"Error generating FTL row {target_row}: {e}")
                ToolRun.objects.create(
                    user=request.user,
                    tool=ToolRun.TOOL_FTL,
                    status=ToolRun.STATUS_FAILED,
                    detail=f"Error writing row {target_row}: {e}"
                )
                return JsonResponse({'error': str(e)}, status=500)
        else:
            errors = {k: v[0] for k, v in form.errors.items()}
            logger.warning(f"Workbook validation failure during FTL processing by {request.user.username}: {errors}")
            return JsonResponse({'error': 'Validation failed', 'field_errors': errors}, status=400)

    # POST: delete row
    if action == 'delete' and request.method == 'POST':
        row_num = int(request.POST.get('row', 0))
        page_data = ftl_logic.get_ftl_page_data(file_path, sheet_name=sheet_name, page=1, page_size=1)
        totals_row = page_data['totals_row'] if page_data else 1000
        if row_num < 2 or row_num >= totals_row:
            return JsonResponse({'error': 'Invalid row number'}, status=400)
        try:
            ftl_logic.clear_ftl_row(file_path, row_num, sheet_name=sheet_name)
            ToolRun.objects.create(
                user=request.user,
                tool=ToolRun.TOOL_FTL,
                status=ToolRun.STATUS_SUCCESS,
                reference=f"Clear Row: {row_num}",
                detail=f"Cleared all FTL shipment details in Row {row_num} on sheet {sheet_name}"
            )
            return JsonResponse({'success': True, 'row': row_num})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # GET: next available row
    if action == 'next_row':
        next_row = ftl_logic.find_next_ftl_row(file_path, sheet_name=sheet_name)
        return JsonResponse({'next_row': next_row})

    return JsonResponse({'error': 'Unknown action'}, status=400)


@staff_required
@tool_permission_required('ftl')
def ftl_download(request):
    from core.services.workbook_manager import WorkbookManager
    wb_obj, file_path, sheet_name = get_active_ftl_workbook()
    
    stream = WorkbookManager.get_file_stream(wb_obj, 'FTL_Shipment_Tracker.xlsx')
    if not stream:
        raise Http404("FTL Shipment Tracker file not found.")
    
    filename = wb_obj.original_name if wb_obj else "FTL_Shipment_Tracker.xlsx"
    logger.info(f"Report downloaded: FTL Tracker '{filename}' by user '{request.user.username}'")
    response = FileResponse(stream, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@staff_required
@tool_permission_required('ftl')
def ftl_settings(request):
    """Manage active FTL shipment workbook and active sheet tab."""
    wb_obj, file_path, current_sheet_name = get_active_ftl_workbook()
    
    from core.services.sheet_parser import get_sheet_names
    sheets = get_sheet_names(file_path)
    if not sheets:
        sheets = ['Sheet1']
    else:
        sheets = ['Sheet1']
        
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'remove':
            FtlWorkbook.objects.filter(is_active=True).update(is_active=False)
            if FtlWorkbook.objects.count() == 0:
                FtlWorkbook.objects.create(
                    original_name='FTL_Shipment_Tracker.xlsx',
                    active_sheet='Sheet1',
                    uploaded_by=request.user,
                    is_active=False
                )
            logger.info(f"Workbook archived/removed: FTL Tracker by user '{request.user.username}'")
            messages.success(request, "FTL shipment sheet removed entirely. Portal is now in empty state.")
            return redirect('ftl_settings')
            
        elif action == 'load_default':
            from core.services.workbook_manager import WorkbookManager
            
            FtlWorkbook.objects.filter(is_active=True).update(is_active=False)
            
            file_name = WorkbookManager.load_default_template('ftl', 'FTL_Shipment_Tracker.xlsx')
            
            wb_obj = FtlWorkbook.objects.create(
                original_name='FTL_Shipment_Tracker.xlsx',
                active_sheet='Sheet1',
                uploaded_by=request.user,
                is_active=True
            )
            wb_obj.file.name = file_name
            wb_obj.save(update_fields=['file'])
            
            logger.info(f"Workbook activated: Default FTL Tracker loaded by user '{request.user.username}'")
            messages.success(request, "Default FTL shipment workbook loaded successfully.")
            return redirect('ftl_settings')
            
        elif action == 'change_sheet':
            form = FtlWorkbookUploadForm(request.POST, sheets=sheets)
            if form.is_valid():
                sheet_sel = form.cleaned_data.get('active_sheet')
                if wb_obj:
                    wb_obj.active_sheet = sheet_sel
                    wb_obj.save(update_fields=['active_sheet'])
                else:
                    from core.services.workbook_manager import WorkbookManager
                    file_name = WorkbookManager.load_default_template('ftl', 'FTL_Shipment_Tracker.xlsx')
                    
                    wb_obj = FtlWorkbook.objects.create(
                        original_name='FTL_Shipment_Tracker.xlsx',
                        active_sheet=sheet_sel,
                        uploaded_by=request.user,
                        is_active=True
                    )
                    wb_obj.file.name = file_name
                    wb_obj.save(update_fields=['file'])
                    
                messages.success(request, f"Active sheet tab changed to '{sheet_sel}'.")
                return redirect('ftl_sheet')
                
        elif action == 'upload':
            form = FtlWorkbookUploadForm(request.POST, request.FILES, sheets=sheets)
            if form.is_valid():
                upload = request.FILES.get('workbook')
                if upload:
                    new_wb = FtlWorkbook.objects.create(
                        file=upload, original_name=upload.name,
                        uploaded_by=request.user, is_active=False
                    )
                    from core.services.sheet_parser import get_sheet_names
                    if new_wb.file:
                        sheetnames = get_sheet_names(new_wb.file.path)
                        if sheetnames:
                            new_wb.active_sheet = sheetnames[0]
                            new_wb.save(update_fields=['active_sheet'])
                    
                    FtlWorkbook.objects.filter(is_active=True).update(is_active=False)
                    new_wb.is_active = True
                    new_wb.save(update_fields=['is_active'])
                    
                    logger.info(f"Workbook uploaded: FTL Tracker '{upload.name}' by user '{request.user.username}'")
                    messages.success(request, f"Uploaded workbook '{upload.name}' is now the active FTL shipment workbook.")
                    return redirect('ftl_settings')
                else:
                    logger.warning(f"Workbook validation failure: No file provided for FTL upload by user '{request.user.username}'")
                    messages.error(request, "Please choose a valid .xlsx file to upload.")
    else:
        form = FtlWorkbookUploadForm(initial={'active_sheet': current_sheet_name}, sheets=sheets)
        
    context = {
        'active': 'ftl',
        'form': form,
        'wb': wb_obj,
        'current_sheet': current_sheet_name,
        'sheets': sheets,
    }
    return render(request, 'core/portal/ftl_settings.html', context)


