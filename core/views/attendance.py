from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404
from core.models import AttendanceWorkbook
from core.forms import AttendanceWorkbookUploadForm
from core.decorators import staff_required, tool_permission_required
from core import attendance as attendance_logic
import os
from core.models import ToolRun
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from core.workbook.locking import workbook_lock
import uuid
import logging

logger = logging.getLogger(__name__)

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
            with workbook_lock(file_path):
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
            
    manual_year = request.POST.get('manual_year') or request.GET.get('manual_year')
    manual_month = request.POST.get('manual_month') or request.GET.get('manual_month')
    
    # Load sheet data
    data = attendance_logic.get_attendance_data(file_path, sheet_name, manual_year, manual_month)
    if not data:
        return render(request, 'core/portal/attendance_form.html', {
            'active': 'attendance',
            'no_sheet': True,
        })
        
    if data.get('requires_manual_date'):
        return render(request, 'core/portal/attendance_form.html', {
            'active': 'attendance',
            'requires_manual_date': True,
            'sheet_name': sheet_name,
            'wb': wb_obj,
            'sheet_names': data.get('sheet_names', [])
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
        'manual_year': data.get('year'),
        'manual_month': data.get('month'),
    }
    return render(request, 'core/portal/attendance_form.html', context)


@staff_required
@tool_permission_required('attendance')
def attendance_download(request):
    from core.services.workbook_manager import WorkbookManager
    wb_obj, file_path, sheet_name = attendance_logic.get_active_attendance_workbook()
    
    stream = WorkbookManager.get_file_stream(wb_obj, 'Attendance_Sheet.xlsx')
    if not stream:
        raise Http404("Attendance workbook file not found.")
        
    filename = wb_obj.original_name if wb_obj else "Attendance_Sheet.xlsx"
    logger.info(f"Report downloaded: Attendance Tracker '{filename}' by user '{request.user.username}'")
    response = FileResponse(stream, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@staff_required
@tool_permission_required('attendance')
def attendance_settings(request):
    """Manage active Attendance workbook and active sheet tab."""
    wb_obj, file_path, current_sheet_name = attendance_logic.get_active_attendance_workbook()
    
    # Read sheets from Excel if file_path exists
    from core.services.sheet_parser import get_sheet_names
    sheets = get_sheet_names(file_path)
    if not sheets:
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
            logger.info(f"Workbook archived/removed: Attendance Tracker by user '{request.user.username}'")
            messages.success(request, "Attendance sheet removed entirely. Portal is now in empty state.")
            return redirect('attendance_settings')
            
        elif action == 'load_default':
            from core.services.workbook_manager import WorkbookManager
            
            AttendanceWorkbook.objects.filter(is_active=True).update(is_active=False)
            
            file_name = WorkbookManager.load_default_template('attendance', 'Attendance_Sheet.xlsx')
            
            wb_obj = AttendanceWorkbook.objects.create(
                original_name='Attendance_Sheet.xlsx',
                active_sheet='JUNE 2026',
                uploaded_by=request.user,
                is_active=True
            )
            wb_obj.file.name = file_name
            wb_obj.save(update_fields=['file'])
            
            from core.services.sheet_parser import get_sheet_names
            if wb_obj.file:
                sheetnames = get_sheet_names(wb_obj.file.path)
                if sheetnames:
                    wb_obj.active_sheet = sheetnames[-1]
                    wb_obj.save(update_fields=['active_sheet'])
                
            logger.info(f"Workbook activated: Default Attendance Tracker loaded by user '{request.user.username}'")
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
                    from core.services.workbook_manager import WorkbookManager
                    file_name = WorkbookManager.load_default_template('attendance', 'Attendance_Sheet.xlsx')
                    
                    wb_obj = AttendanceWorkbook.objects.create(
                        original_name='Attendance_Sheet.xlsx',
                        active_sheet=sheet_sel,
                        uploaded_by=request.user,
                        is_active=True
                    )
                    wb_obj.file.name = file_name
                    wb_obj.save(update_fields=['file'])
                    
                messages.success(request, f"Active sheet tab changed to '{sheet_sel}'.")
                return redirect('attendance_sheet')
                
        elif action == 'upload':
            form = AttendanceWorkbookUploadForm(request.POST, request.FILES, sheets=sheets)
            if form.is_valid():
                upload = request.FILES.get('workbook')
                if upload:
                    original_name = upload.name
                    ext = os.path.splitext(original_name)[1]
                    upload.name = f"attendance_{uuid.uuid4().hex}{ext}"
                    new_wb = AttendanceWorkbook.objects.create(
                        file=upload, original_name=original_name,
                        uploaded_by=request.user, is_active=False
                    )
                    
                    from core.services.sheet_parser import get_sheet_names
                    if new_wb.file:
                        sheetnames = get_sheet_names(new_wb.file.path)
                        if sheetnames:
                            new_wb.active_sheet = sheetnames[-1]
                            new_wb.save(update_fields=['active_sheet'])
                    
                    AttendanceWorkbook.objects.filter(is_active=True).update(is_active=False)
                    new_wb.is_active = True
                    new_wb.save(update_fields=['is_active'])
                    
                    logger.info(f"Workbook uploaded: Attendance Tracker '{original_name}' by user '{request.user.username}'")
                    messages.success(request, f"Uploaded workbook '{original_name}' is now the active attendance workbook.")
                    return redirect('attendance_settings')
                else:
                    logger.warning(f"Workbook validation failure: No file provided for Attendance upload by user '{request.user.username}'")
                    messages.error(request, "Please choose a valid .xlsx file to upload.")
                    
        elif action == 'update_salary_config':
            from core.models import SalaryConfig
            from core.forms import SalaryConfigForm
            config = SalaryConfig.get_solo()
            salary_form = SalaryConfigForm(request.POST, instance=config)
            if salary_form.is_valid():
                salary_form.save()
                messages.success(request, "Salary configuration updated successfully.")
                return redirect('attendance_settings')
    else:
        form = AttendanceWorkbookUploadForm(initial={'active_sheet': current_sheet_name}, sheets=sheets)
        
    from core.models import SalaryConfig
    from core.forms import SalaryConfigForm
    salary_form = SalaryConfigForm(instance=SalaryConfig.get_solo())
        
    context = {
        'active': 'attendance',
        'form': form,
        'salary_form': salary_form,
        'wb': wb_obj,
        'current_sheet': current_sheet_name,
        'sheets': sheets,
    }
    return render(request, 'core/portal/attendance_settings.html', context)



@staff_required
@tool_permission_required('attendance')
@never_cache
def salary_calculator(request):
    from core.models import EmployeeSalaryOverride, SalaryConfig
    from decimal import Decimal

    wb_obj, file_path, sheet_name = attendance_logic.get_active_attendance_workbook()
    
    if not file_path or not os.path.exists(file_path):
        return render(request, 'core/portal/attendance_salary.html', {
            'active': 'attendance',
            'no_sheet': True,
        })

    manual_year = request.POST.get('manual_year') or request.GET.get('manual_year')
    manual_month = request.POST.get('manual_month') or request.GET.get('manual_month')
    
    data = attendance_logic.get_attendance_data(file_path, sheet_name, manual_year, manual_month)
    if not data:
        return render(request, 'core/portal/attendance_salary.html', {
            'active': 'attendance',
            'no_sheet': True,
        })
        
    if data.get('requires_manual_date'):
        return render(request, 'core/portal/attendance_salary.html', {
            'active': 'attendance',
            'requires_manual_date': True,
            'sheet_name': sheet_name,
            'wb': wb_obj,
            'sheet_names': data.get('sheet_names', [])
        })
        
    if request.method == 'POST':
        # Save salaries
        for emp in data['employees']:
            emp_name = emp['name']
            inc_val = request.POST.get(f'override_inc_{emp_name}')
            allow_val = request.POST.get(f'override_allow_{emp_name}')
            adv_val = request.POST.get(f'override_adv_{emp_name}')
            lwf_val = request.POST.get(f'override_lwf_{emp_name}')
            oth_val = request.POST.get(f'override_other_{emp_name}')
            csh_val = request.POST.get(f'override_cash_{emp_name}')
            
            if any(v is not None for v in [inc_val, allow_val, adv_val, lwf_val, oth_val, csh_val]):
                try:
                    def parse_dec(val):
                        if val is None or val.strip() == '': return Decimal('0.00')
                        return Decimal(val.strip())
                        
                    EmployeeSalaryOverride.objects.update_or_create(
                        employee_name=emp_name,
                        defaults={
                            'adhoc_salary_increase_pct': parse_dec(inc_val),
                            'adhoc_allowance_monthly_amount': parse_dec(allow_val),
                            'advance': parse_dec(adv_val),
                            'lwf': parse_dec(lwf_val),
                            'other_deduction': parse_dec(oth_val),
                            'cash_payment': parse_dec(csh_val)
                        }
                    )
                except Exception as e:
                    logger.error(f"Workbook processing failure for salary overrides of {emp_name}: {e}")
                    messages.error(request, f"Invalid override values for {emp_name}: {e}")
                    
        messages.success(request, "Salaries saved successfully.")
        manual_year = request.POST.get('manual_year')
        manual_month = request.POST.get('manual_month')
        redirect_url = reverse('salary_calculator')
        if manual_year and manual_month:
            redirect_url += f"?manual_year={manual_year}&manual_month={manual_month}"
        return redirect(redirect_url)

    # Ensure all employees in the sheet have an EmployeeSalaryOverride record
    employee_names = [emp['name'] for emp in data['employees']]
    existing_salaries = EmployeeSalaryOverride.objects.filter(employee_name__in=employee_names).values_list('employee_name', flat=True)
    for name in employee_names:
        if name not in existing_salaries:
            EmployeeSalaryOverride.objects.get_or_create(employee_name=name)

    salary_data = attendance_logic.calculate_salary_data(data)
    
    context = {
        'active': 'attendance',
        'sheet_name': sheet_name,
        'wb': wb_obj,
        'salary_data': salary_data,
        'sheet_names': data['sheet_names'],
        'manual_year': data.get('year'),
        'manual_month': data.get('month'),
    }
    return render(request, 'core/portal/attendance_salary.html', context)


@staff_required
@tool_permission_required('attendance')
def salary_calculator_export(request):
    from django.http import HttpResponse
    from core.services.exports.attendance import generate_salary_export
    from pathlib import Path

    wb_obj, file_path, sheet_name = attendance_logic.get_active_attendance_workbook()
    if not file_path or not Path(file_path).exists():
        messages.error(request, "Attendance workbook file not found.")
        return redirect('salary_calculator')

    manual_year = request.GET.get('manual_year')
    manual_month = request.GET.get('manual_month')
    
    data = attendance_logic.get_attendance_data(file_path, sheet_name, manual_year, manual_month)
    if not data or data.get('requires_manual_date'):
        messages.error(request, "Cannot export: Invalid sheet date or data.")
        return redirect('salary_calculator')

    salary_data = attendance_logic.calculate_salary_data(data)

    buffer = generate_salary_export(sheet_name, salary_data)
    
    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="Salary_{sheet_name}.xlsx"'
    logger.info(f"Report generated and downloaded: Salary '{sheet_name}' by user '{request.user.username}'")
    return response
