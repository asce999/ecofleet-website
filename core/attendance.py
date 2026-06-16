import os
import calendar
import datetime
import openpyxl
from django.conf import settings
from openpyxl.utils import get_column_letter

def get_days_in_sheet(sheet_name):
    # Try parsing sheet_name like "JUNE 2026" or "May 2026"
    parts = sheet_name.strip().split()
    if len(parts) == 2:
        month_name, year_str = parts
        try:
            year = int(year_str)
            try:
                month = datetime.datetime.strptime(month_name, "%B").month
            except ValueError:
                month = datetime.datetime.strptime(month_name, "%b").month
            return calendar.monthrange(year, month)[1]
        except Exception:
            pass
    return 30  # Fallback

def get_active_attendance_workbook():
    from core.models import AttendanceWorkbook
    wb_count = AttendanceWorkbook.objects.count()
    if wb_count > 0:
        wb_obj = AttendanceWorkbook.active()
        if not wb_obj:
            return None, None, None
        return wb_obj, wb_obj.file.path, wb_obj.active_sheet
    else:
        file_path = os.path.join(settings.BASE_DIR, 'Attendance_Sheet.xlsx')
        sheet_name = 'JUNE 2026'
        if os.path.exists(file_path):
            try:
                wb = openpyxl.load_workbook(file_path, read_only=True)
                if wb.sheetnames:
                    sheet_name = wb.sheetnames[-1]
            except Exception:
                pass
        return None, file_path, sheet_name

def get_attendance_data(file_path, sheet_name):
    if not os.path.exists(file_path):
        return None
        
    wb = openpyxl.load_workbook(file_path, data_only=True)
    if sheet_name not in wb.sheetnames:
        sheet_name = wb.sheetnames[-1] if wb.sheetnames else None
        if not sheet_name:
            return None
            
    sheet = wb[sheet_name]
    
    # 1. Determine number of days in the month
    days_in_month = get_days_in_sheet(sheet_name)
    
    # 2. Find STAFF NAME and PHONE NUMBER column indices
    staff_col = 1
    phone_col = None
    for c in range(1, sheet.max_column + 1):
        h_val = sheet.cell(row=1, column=c).value
        if h_val:
            h_str = str(h_val).strip().lower()
            if h_str == 'staff name':
                staff_col = c
            elif h_str == 'phone number':
                phone_col = c

    # 3. Identify holidays/weekly offs for days
    day_headers = {}
    for d in range(1, days_in_month + 1):
        col_idx = d + staff_col
        h_val = sheet.cell(row=1, column=col_idx).value
        is_holiday = False
        if h_val:
            if str(h_val).strip().upper() == 'HD':
                is_holiday = True
        day_headers[d] = {
            'col_idx': col_idx,
            'is_holiday': is_holiday,
            'header_val': h_val if h_val is not None else ""
        }

    # 4. Extract employees and their attendance
    employees = []
    for r in range(2, sheet.max_row + 1):
        name = sheet.cell(row=r, column=staff_col).value
        if name is None or str(name).strip() == "":
            continue
            
        name = str(name).strip()
        phone = ""
        if phone_col:
            phone_val = sheet.cell(row=r, column=phone_col).value
            if phone_val is not None:
                phone = str(phone_val).strip()
                
        attendance = {}
        for d in range(1, days_in_month + 1):
            col_idx = day_headers[d]['col_idx']
            val = sheet.cell(row=r, column=col_idx).value
            status = ""
            if val is not None:
                status = str(val).strip().upper()
            attendance[d] = status
            
        employees.append({
            'row_idx': r,
            'name': name,
            'phone': phone,
            'attendance': attendance
        })
        
    return {
        'sheet_name': sheet_name,
        'days_in_month': days_in_month,
        'day_headers': day_headers,
        'employees': employees,
        'sheet_names': wb.sheetnames
    }

def save_attendance(file_path, sheet_name, post_data):
    if not os.path.exists(file_path):
        raise FileNotFoundError("Attendance sheet file not found.")
        
    wb = openpyxl.load_workbook(file_path, data_only=False)
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"Sheet tab '{sheet_name}' not found in workbook.")
        
    sheet = wb[sheet_name]
    
    # Get column mapping
    staff_col = 1
    for c in range(1, sheet.max_column + 1):
        h_val = sheet.cell(row=1, column=c).value
        if h_val and str(h_val).strip().lower() == 'staff name':
            staff_col = c
            break

    # Look for inputs like: attendance_{row_idx}_{day}
    modified = False
    for key, val in post_data.items():
        if key.startswith('attendance_'):
            parts = key.split('_')
            if len(parts) == 3:
                try:
                    row_idx = int(parts[1])
                    day = int(parts[2])
                    col_idx = day + staff_col
                    
                    # Clean the status value
                    status = str(val).strip().upper()
                    if status in ['', 'EMPTY', 'NONE']:
                        new_val = None
                    else:
                        new_val = status
                        
                    current_val = sheet.cell(row=row_idx, column=col_idx).value
                    # Check if actually modified to reduce writes
                    current_str = str(current_val).strip().upper() if current_val is not None else ""
                    new_str = new_val if new_val is not None else ""
                    if current_str != new_str:
                        sheet.cell(row=row_idx, column=col_idx).value = new_val
                        modified = True
                except (ValueError, TypeError):
                    pass
                    
    if modified:
        wb.save(file_path)
    return modified
