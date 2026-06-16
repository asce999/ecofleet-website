from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404
from core.models import AttendanceWorkbook
from core.forms import AttendanceWorkbookUploadForm
from core.decorators import staff_required, tool_permission_required
from core import attendance as attendance_logic
import os


@staff_required
@tool_permission_required('attendance')
@never_cache
def attendance_sheet(request):
    from django.urls import reverse
    wb_obj, file_path, sheet_name = attendance_logic.get_active_attendance_workbook()
    
    if not file_path or not os.path.exists(file_path):
        return render(request, 'core/portal/attendance_form.html', {
            'active': 'attendance',
            'no_sheet': True,
        })
        
    if request.method == 'POST':
        try:
            modified = attendance_logic.save_attendance(file_path, sheet_name, request.POST)
            if modified:
                ToolRun.objects.create(
                    user=request.user,
                    tool=ToolRun.TOOL_ATTENDANCE,
                    status=ToolRun.STATUS_SUCCESS,
                    reference=f"Update: {sheet_name}",
                    detail=f"Updated attendance sheet '{sheet_name}'"
                )
                messages.success(request, "Attendance updated successfully.")
                return redirect(reverse('attendance_sheet') + '?success=1')
            else:
                messages.info(request, "No changes were made to the attendance sheet.")
                return redirect('attendance_sheet')
        except Exception as e:
            messages.error(request, f"Failed to save attendance: {e}")
            return redirect('attendance_sheet')
            
    # Load sheet data
    data = attendance_logic.get_attendance_data(file_path, sheet_name)
    if not data:
        return render(request, 'core/portal/attendance_form.html', {
            'active': 'attendance',
            'no_sheet': True,
        })
        
    days_list = list(range(1, data['days_in_month'] + 1))
    days_info_list = []
    for d in days_list:
        days_info_list.append({
            'day': d,
            'is_holiday': data['day_headers'][d]['is_holiday']
        })
        
    employees_list = []
    for emp in data['employees']:
        days_attendance = []
        for d in days_list:
            days_attendance.append({
                'day': d,
                'status': emp['attendance'].get(d, ''),
                'is_holiday': data['day_headers'][d]['is_holiday']
            })
        employees_list.append({
            'row_idx': emp['row_idx'],
            'name': emp['name'],
            'phone': emp['phone'],
            'days_attendance': days_attendance
        })
        
    context = {
        'active': 'attendance',
        'sheet_name': data['sheet_name'],
        'days_in_month': data['days_in_month'],
        'days_info_list': days_info_list,
        'employees': employees_list,
        'sheet_names': data['sheet_names'],
        'wb': wb_obj,
        'success': request.GET.get('success') == '1',
    }
    return render(request, 'core/portal/attendance_form.html', context)


@staff_required
@tool_permission_required('attendance')
def attendance_download(request):
    wb_obj, file_path, sheet_name = attendance_logic.get_active_attendance_workbook()
    if not file_path or not os.path.exists(file_path):
        raise Http404("Attendance workbook file not found.")
        
    filename = wb_obj.original_name if wb_obj else "Attendance_Sheet.xlsx"
    response = FileResponse(open(file_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@staff_required
@tool_permission_required('attendance')
def attendance_settings(request):
    """Manage active Attendance workbook and active sheet tab."""
    wb_obj, file_path, current_sheet_name = attendance_logic.get_active_attendance_workbook()
    
    # Read sheets from Excel if file_path exists
    sheets = []
    if file_path and os.path.exists(file_path):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, read_only=True)
            sheets = wb.sheetnames
        except Exception:
            sheets = ['JUNE 2026']
    else:
        sheets = ['JUNE 2026']
        
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'remove':
            AttendanceWorkbook.objects.filter(is_active=True).update(is_active=False)
            if AttendanceWorkbook.objects.count() == 0:
                AttendanceWorkbook.objects.create(
                    original_name='Attendance_Sheet.xlsx',
                    active_sheet='JUNE 2026',
                    uploaded_by=request.user,
                    is_active=False
                )
            messages.success(request, "Attendance sheet removed entirely. Portal is now in empty state.")
            return redirect('attendance_settings')
            
        elif action == 'load_default':
            import shutil
            root_file_path = os.path.join(settings.BASE_DIR, 'Attendance_Sheet.xlsx')
            target_dir = os.path.join(settings.MEDIA_ROOT, 'attendance')
            os.makedirs(target_dir, exist_ok=True)
            dest_path = os.path.join(target_dir, 'Attendance_Sheet.xlsx')
            shutil.copy2(root_file_path, dest_path)
            
            AttendanceWorkbook.objects.filter(is_active=True).update(is_active=False)
            
            wb_obj = AttendanceWorkbook.objects.create(
                original_name='Attendance_Sheet.xlsx',
                active_sheet='JUNE 2026',
                uploaded_by=request.user,
                is_active=True
            )
            wb_obj.file.name = 'attendance/Attendance_Sheet.xlsx'
            wb_obj.save(update_fields=['file'])
            
            try:
                wb = openpyxl.load_workbook(dest_path, read_only=True)
                if wb.sheetnames:
                    wb_obj.active_sheet = wb.sheetnames[-1]
                    wb_obj.save(update_fields=['active_sheet'])
            except Exception:
                pass
                
            messages.success(request, "Default attendance workbook loaded successfully.")
            return redirect('attendance_settings')
            
        elif action == 'change_sheet':
            form = AttendanceWorkbookUploadForm(request.POST, sheets=sheets)
            if form.is_valid():
                sheet_sel = form.cleaned_data.get('active_sheet')
                if wb_obj:
                    wb_obj.active_sheet = sheet_sel
                    wb_obj.save(update_fields=['active_sheet'])
                else:
                    import shutil
                    root_file_path = os.path.join(settings.BASE_DIR, 'Attendance_Sheet.xlsx')
                    target_dir = os.path.join(settings.MEDIA_ROOT, 'attendance')
                    os.makedirs(target_dir, exist_ok=True)
                    dest_path = os.path.join(target_dir, 'Attendance_Sheet.xlsx')
                    shutil.copy2(root_file_path, dest_path)
                    
                    wb_obj = AttendanceWorkbook.objects.create(
                        original_name='Attendance_Sheet.xlsx',
                        active_sheet=sheet_sel,
                        uploaded_by=request.user,
                        is_active=True
                    )
                    wb_obj.file.name = 'attendance/Attendance_Sheet.xlsx'
                    wb_obj.save(update_fields=['file'])
                    
                messages.success(request, f"Active sheet tab changed to '{sheet_sel}'.")
                return redirect('attendance_sheet')
                
        elif action == 'upload':
            form = AttendanceWorkbookUploadForm(request.POST, request.FILES, sheets=sheets)
            if form.is_valid():
                upload = request.FILES.get('workbook')
                if upload:
                    new_wb = AttendanceWorkbook.objects.create(
                        file=upload, original_name=upload.name,
                        uploaded_by=request.user, is_active=False
                    )
                    
                    try:
                        import openpyxl
                        temp_wb = openpyxl.load_workbook(new_wb.file.path, read_only=True)
                        uploaded_sheets = temp_wb.sheetnames
                        default_sheet = uploaded_sheets[-1] if uploaded_sheets else 'JUNE 2026'
                    except Exception:
                        default_sheet = 'JUNE 2026'
                        
                    new_wb.active_sheet = default_sheet
                    new_wb.save(update_fields=['active_sheet'])
                    
                    AttendanceWorkbook.objects.filter(is_active=True).update(is_active=False)
                    new_wb.is_active = True
                    new_wb.save(update_fields=['is_active'])
                    
                    messages.success(request, f"Uploaded workbook '{upload.name}' is now the active attendance workbook.")
                    return redirect('attendance_settings')
                else:
                    messages.error(request, "Please choose a valid .xlsx file to upload.")
    else:
        form = AttendanceWorkbookUploadForm(initial={'active_sheet': current_sheet_name}, sheets=sheets)
        
    context = {
        'active': 'attendance',
        'form': form,
        'wb': wb_obj,
        'current_sheet': current_sheet_name,
        'sheets': sheets,
    }
    return render(request, 'core/portal/attendance_settings.html', context)


