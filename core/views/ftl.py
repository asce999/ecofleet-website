from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect
from django.db import transaction
from django.http import FileResponse, Http404
from core.models import FtlWorkbook
from core.forms import FtlShipmentForm, FtlWorkbookUploadForm
from core.decorators import staff_required, tool_permission_required
from core import ftl as ftl_logic
import os
import datetime
from core.models import ToolRun, MigrationFeatureFlags, Shipment
from django.contrib import messages
from core.utils.parsing import safe_int
from core.workbook.locking import workbook_lock
import uuid
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
        file_path = os.path.join(settings.BASE_DIR, 'core', 'templates_default', 'FTL_Shipment_Tracker.xlsx')
        sheet_name = 'Sheet1'
        return None, file_path, sheet_name


def _get_db_ftl_page_data(page=1, page_size=20, target_row=None):
    shipments = Shipment.objects.filter(shipment_type='FTL').order_by('dispatch_date', 'source_key')
    total_rows = shipments.count()
    total_pages = max(1, (total_rows + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_shipments = shipments[start_idx:end_idx]

    columns = [
        'Date of Booking', 'ETD', 'Date of Delivery', 'Consignor', 'From Location',
        'Consignee', 'LR Number', 'To Location', 'Vehicle Number', 'Vendor', 'Serial'
    ]

    def format_date(d):
        if not d: return ""
        return d.strftime('%d-%b-%y')

    rows = []
    for i, s in enumerate(page_shipments):
        row_num = start_idx + i + 2
        cells = [
            format_date(s.dispatch_date),
            "", # ETD
            "", # Delivery Date
            s.metadata.get('consignor', ''),
            s.origin,
            s.metadata.get('consignee', ''),
            s.metadata.get('lr_number', ''),
            s.destination,
            s.vehicle.registration_number if s.vehicle else '',
            s.metadata.get('vendor', ''),
            row_num - 1 # Serial
        ]
        rows.append({'row_num': row_num, 'cells': cells})

    preview = {
        'columns': columns,
        'rows': rows,
        'total_rows': total_rows,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    }

    totals_row = total_rows + 2
    next_row = target_row if target_row else totals_row

    row_values = {}
    if next_row < totals_row:
        idx = next_row - 2
        if 0 <= idx < total_rows:
            s = shipments[idx]
            row_values = {
                'row_num': next_row,
                'booking_date': s.dispatch_date,
                'etd': None,
                'delivery_date': None,
                'consignor': s.metadata.get('consignor', ''),
                'origin': s.origin,
                'consignee': s.metadata.get('consignee', ''),
                'lr_number': s.metadata.get('lr_number', ''),
                'destination': s.destination,
                'vehicle_number': s.vehicle.registration_number if s.vehicle else '',
                'vendor': s.metadata.get('vendor', ''),
            }

    return {
        'mapping': {},
        'totals_row': totals_row,
        'next_row': next_row,
        'row_values': row_values,
        'preview': preview,
    }


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

    page = safe_int(request.GET.get('page', 1), 1)
    
    flags = MigrationFeatureFlags.get_solo()
    if flags.use_database_reads:
        page_data = _get_db_ftl_page_data(page=page, page_size=20)
    else:
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
    
    flags = MigrationFeatureFlags.get_solo()
    use_db = flags.use_database_reads

    # GET: fetch row data for editing
    if action == 'get_row':
        row_num = safe_int(request.GET.get('row', 0), 0)
        if row_num < 2:
            return JsonResponse({'error': 'Invalid row'}, status=400)
            
        if use_db:
            page_data = _get_db_ftl_page_data(page=1, page_size=1, target_row=row_num)
            row_data = page_data['row_values']
        else:
            row_data = ftl_logic.get_ftl_row_values(file_path, row_num, sheet_name=sheet_name)
        for key in ['booking_date', 'etd', 'delivery_date']:
            val = row_data.get(key)
            if isinstance(val, (datetime.datetime, datetime.date)):
                row_data[key] = val.strftime('%Y-%m-%d')
        return JsonResponse({'row_data': row_data})

    # GET: paginated preview
    if action == 'preview':
        page = safe_int(request.GET.get('page', 1), 1)
        if use_db:
            page_data = _get_db_ftl_page_data(page=page, page_size=20)
            preview = page_data['preview']
        else:
            preview = ftl_logic.get_ftl_preview(file_path, sheet_name=sheet_name, page=page, page_size=20)
        return JsonResponse({'preview': preview})

    # POST: save row
    if action == 'save' and request.method == 'POST':
        form = FtlShipmentForm(request.POST)
        if form.is_valid():
            row_data = form.cleaned_data
            target_row = row_data['row_num']
            try:
                with workbook_lock(file_path):
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
        row_num = safe_int(request.POST.get('row', 0), 0)
        if use_db:
            page_data = _get_db_ftl_page_data(page=1, page_size=1)
        else:
            page_data = ftl_logic.get_ftl_page_data(file_path, sheet_name=sheet_name, page=1, page_size=1)
        totals_row = page_data['totals_row'] if page_data else 1000
        if row_num < 2 or row_num >= totals_row:
            return JsonResponse({'error': 'Invalid row number'}, status=400)
        try:
            with workbook_lock(file_path):
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
        if use_db:
            next_row = Shipment.objects.filter(shipment_type='FTL').count() + 2
        else:
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
        
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'remove':
            with transaction.atomic():
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
            
            file_name = WorkbookManager.load_default_template('ftl', 'FTL_Shipment_Tracker.xlsx')
            
            with transaction.atomic():
                FtlWorkbook.objects.filter(is_active=True).update(is_active=False)
                
                wb_obj = FtlWorkbook.objects.create(
                    original_name='FTL_Shipment_Tracker.xlsx',
                    active_sheet='Sheet1',
                    uploaded_by=request.user,
                    is_active=True
                )
                wb_obj.file.name = file_name
                wb_obj.save(update_fields=['file'])
            
            logger.info(f"Workbook activated: Default FTL Tracker loaded by user '{request.user.username}'")
            try:
                from core.models import SystemEvent
                SystemEvent.objects.create(
                    component='ftl',
                    event_type='workbook_activated',
                    title='Default FTL Tracker Loaded',
                    message=f"Default FTL Tracker loaded by {request.user.username}",
                    request_id=getattr(request, 'request_id', None),
                    user=request.user,
                    metadata={'file': file_name}
                )
            except Exception as e:
                logger.error(f"Failed to log SystemEvent: {e}")
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
                    with transaction.atomic():
                        wb_obj = FtlWorkbook.objects.create(
                            original_name='FTL_Shipment_Tracker.xlsx',
                            active_sheet=sheet_sel,
                            uploaded_by=request.user,
                            is_active=True
                        )
                        wb_obj.file.name = file_name
                        wb_obj.save(update_fields=['file'])
                    try:
                        from core.models import SystemEvent
                        SystemEvent.objects.create(
                            component='ftl',
                            event_type='workbook_activated',
                            title='New FTL Tracker Initialized',
                            message=f"Default FTL Tracker initialized with sheet '{sheet_sel}' by {request.user.username}",
                            request_id=getattr(request, 'request_id', None),
                            user=request.user,
                            metadata={'file': file_name, 'sheet': sheet_sel}
                        )
                    except Exception as e:
                        logger.error(f"Failed to log SystemEvent: {e}")
                    
                messages.success(request, f"Active sheet tab changed to '{sheet_sel}'.")
                return redirect('ftl_sheet')
                
        elif action == 'upload':
            form = FtlWorkbookUploadForm(request.POST, request.FILES, sheets=sheets)
            if form.is_valid():
                upload = request.FILES.get('workbook')
                if upload:
                    original_name = upload.name
                    ext = os.path.splitext(original_name)[1]
                    upload.name = f"ftl_{uuid.uuid4().hex}{ext}"
                    new_wb = FtlWorkbook.objects.create(
                        file=upload, original_name=original_name,
                        uploaded_by=request.user, is_active=False
                    )
                    from core.services.sheet_parser import get_sheet_names
                    if new_wb.file:
                        sheetnames = get_sheet_names(new_wb.file.path)
                        if sheetnames:
                            new_wb.active_sheet = sheetnames[0]
                            new_wb.save(update_fields=['active_sheet'])
                    
                    with transaction.atomic():
                        FtlWorkbook.objects.filter(is_active=True).update(is_active=False)
                        new_wb.is_active = True
                        new_wb.save(update_fields=['is_active'])
                    
                    # Phase 3 Shadow Importer Hook
                    from core.models import MigrationFeatureFlags, ImportJob
                    import os
                    flags = MigrationFeatureFlags.get_solo()
                    if flags.use_database_importer:
                        import_job = ImportJob.objects.create(
                            workbook_type='FTL',
                            status='PENDING',
                            uploaded_by=request.user
                        )
                        if os.environ.get('CELERY_BROKER_URL'):
                            from core.tasks import process_ftl_import
                            process_ftl_import.delay(import_job.id, new_wb.file.path)
                        else:
                            from core.importers.excel_importer import ExcelImporter
                            import threading
                            importer = ExcelImporter()
                            thread = threading.Thread(target=importer.process_ftl_workbook, args=(import_job.id, new_wb.file.path))
                            thread.start()
                    
                    logger.info(f"Workbook uploaded: FTL Tracker '{original_name}' by user '{request.user.username}'")
                    try:
                        from core.models import SystemEvent
                        SystemEvent.objects.create(
                            component='ftl',
                            event_type='workbook_activated',
                            title='New FTL Tracker Uploaded',
                            message=f"Workbook '{original_name}' uploaded and activated by {request.user.username}",
                            request_id=getattr(request, 'request_id', None),
                            user=request.user,
                            metadata={'original_name': original_name, 'file': new_wb.file.name}
                        )
                    except Exception as e:
                        logger.error(f"Failed to log SystemEvent: {e}")

                    messages.success(request, f"Uploaded workbook '{original_name}' is now the active FTL shipment workbook.")
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


