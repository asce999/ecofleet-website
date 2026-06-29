import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecofleet.settings')
django.setup()

from core.attendance import get_attendance_data, calculate_salary_data

# The file might be in media directory, or root. The active one is in AttendanceWorkbook
from core.models import AttendanceWorkbook
wb_obj = AttendanceWorkbook.objects.filter(is_active=True).first()
if wb_obj and wb_obj.file:
    file_path = wb_obj.file.path
else:
    file_path = r"C:\Users\ardcr\Desktop\EcoFleetExpress\Attendance_Sheet.xlsx"

data = get_attendance_data(file_path, "May 2026")
result = calculate_salary_data(data)

found = False
for emp in result['employees']:
    if "AMOL" in emp['name'].upper() and "MASKAR" in emp['name'].upper():
        found = True
        print(f"Name: {emp['name']}")
        print(f"Payable Days: {emp['payable_days']}")
        print(f"Extra Days: {emp['extra_days']}")
        print(f"Total A: {emp['total_a']}")
        print(f"Total B: {emp['total_b']}")
        print(f"Sub Total Deductions: {emp['sub_total_deductions']}")
        print(f"Net Payment: {emp['net_payment']}")
        break

if not found:
    print("Amol Maskar not found in May 2026 sheet.")
