from django.test import TestCase
from decimal import Decimal
from core.attendance import calculate_salary_data

class SalaryCalcTests(TestCase):
    def test_calculate_salary_data(self):
        # Simple test data simulating attendance parsing output
        attendance_data = {
            'year': 2026,
            'month': 2,
            'employees': [
                {
                    'name': 'TEST EMPLOYEE',
                    'department': 'TEST DEPT',
                    'emp_id': '123',
                    'esic_no': 'E123',
                    'pf_no': 'P123',
                    'uan_no': 'U123',
                    'payable_days': Decimal('26.0'),
                    'extra_days': Decimal('0.0'),
                    'attendance': {},
                }
            ]
        }
        
        result = calculate_salary_data(attendance_data)
        
        self.assertEqual(len(result['employees']), 1)
        emp_res = result['employees'][0]
        
        self.assertEqual(emp_res['name'], 'TEST EMPLOYEE')
        # Checking keys exist
        self.assertIn('total_a', emp_res)
        self.assertIn('total_b', emp_res)
        self.assertIn('pf', emp_res)
        self.assertIn('esic_employee', emp_res)
        self.assertIn('pt', emp_res)
        self.assertIn('net_payment', emp_res)
