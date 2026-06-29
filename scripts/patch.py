import os

file_path = 'core/views/attendance.py'
with open(file_path, 'r') as f:
    content = f.read()

# 1. Update attendance_sheet view reading data
old1 = '''    # Load sheet data
    data = attendance_logic.get_attendance_data(file_path, sheet_name)
    if not data:
        return render(request, 'core/portal/attendance_form.html', {
            'active': 'attendance',
            'no_sheet': True,
        })'''
new1 = '''    manual_year = request.POST.get('manual_year') or request.GET.get('manual_year')
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
        })'''
content = content.replace(old1, new1)

# 2. Update attendance_sheet view context
old2 = '''    context = {
        'active': 'attendance',
        'sheet_name': data['sheet_name'],
        'days_in_month': data['days_in_month'],
        'days_info_list': days_info_list,
        'employees': employees_list,
        'sheet_names': data['sheet_names'],
        'wb': wb_obj,
        'success': request.GET.get('success') == '1',
    }'''
new2 = '''    context = {
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
    }'''
content = content.replace(old2, new2)

# 3. Update salary_calculator view reading data
old3 = '''    data = attendance_logic.get_attendance_data(file_path, sheet_name)
    if not data:
        return render(request, 'core/portal/attendance_salary.html', {
            'active': 'attendance',
            'no_sheet': True,
        })'''
new3 = '''    manual_year = request.POST.get('manual_year') or request.GET.get('manual_year')
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
        })'''
content = content.replace(old3, new3)

# 4. Update salary_calculator view redirect
old4 = '''        messages.success(request, "Salaries saved successfully.")
        return redirect('salary_calculator')'''
new4 = '''        messages.success(request, "Salaries saved successfully.")
        manual_year = request.POST.get('manual_year')
        manual_month = request.POST.get('manual_month')
        redirect_url = reverse('salary_calculator')
        if manual_year and manual_month:
            redirect_url += f"?manual_year={manual_year}&manual_month={manual_month}"
        return redirect(redirect_url)'''
content = content.replace(old4, new4)

# 5. Update salary_calculator view context
old5 = '''    context = {
        'active': 'attendance',
        'sheet_name': sheet_name,
        'wb': wb_obj,
        'salary_data': salary_data,
        'sheet_names': data['sheet_names']
    }'''
new5 = '''    context = {
        'active': 'attendance',
        'sheet_name': sheet_name,
        'wb': wb_obj,
        'salary_data': salary_data,
        'sheet_names': data['sheet_names'],
        'manual_year': data.get('year'),
        'manual_month': data.get('month'),
    }'''
content = content.replace(old5, new5)

# 6. Update salary_calculator_export view
old6 = '''    data = attendance_logic.get_attendance_data(file_path, sheet_name)
    if not data:
        messages.error(request, "No attendance data available.")
        return redirect('salary_calculator')'''
new6 = '''    manual_year = request.GET.get('manual_year')
    manual_month = request.GET.get('manual_month')
    
    data = attendance_logic.get_attendance_data(file_path, sheet_name, manual_year, manual_month)
    if not data or data.get('requires_manual_date'):
        messages.error(request, "Cannot export: Invalid sheet date or data.")
        return redirect('salary_calculator')'''
content = content.replace(old6, new6)

with open(file_path, 'w') as f:
    f.write(content)
print("Done")
