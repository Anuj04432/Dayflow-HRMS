# -*- coding: utf-8 -*-
"""
Dayflow HRMS - Member 3 (Employee Profile & Payroll) Unit Tests
==============================================================
Validates:
1. Permitted profile field editing rules (Employees vs HR)
2. Salary gross and net take-home computations
3. Salary validation constraints (no negative numbers)
4. Role-based payroll visibility and permissions
"""

import unittest
from datetime import date


class MockUser:
    def __init__(self, user_id=1, role='employee', is_admin=False):
        self.id = user_id
        self.dayflow_role = role
        self.login = 'hr@dayflow.com' if role == 'hr' else 'emp@dayflow.com'
        self._admin_flag = is_admin

    def _is_admin(self):
        return self._admin_flag

    def has_group(self, group_name):
        if self._admin_flag:
            return True
        if self.dayflow_role == 'hr' and 'group_dayflow_hr' in group_name:
            return True
        if 'group_dayflow_employee' in group_name:
            return True
        return False


class MockEmployeeRecord:
    def __init__(self, emp_id=1, name='Alex Johnson', user=None):
        self.id = emp_id
        self.name = name
        self.employee_code = f"DF{emp_id:04d}"
        self.work_email = 'alex@dayflow.com'
        self.phone = '+1 555-0123'
        self.address = '123 Tech Park, Bengaluru'
        self.job_title = 'Software Engineer'
        self.department_name = 'Engineering'
        self.image_1920 = None
        self.status = 'active'
        self.join_date = date.today()
        self.user_id = user or MockUser(user_id=emp_id, role='employee')

    def update_permitted_profile(self, user, vals):
        """Simulates DayflowEmployee.update_permitted_profile()"""
        is_hr = (
            user._is_admin() or
            user.id == 1 or
            user.login == 'admin' or
            getattr(user, 'dayflow_role', None) == 'hr' or
            user.has_group('dayflow.group_dayflow_hr')
        )
        if not is_hr:
            allowed_fields = {'phone', 'address', 'image_1920'}
            attempted = set(vals.keys())
            disallowed = attempted - allowed_fields
            if disallowed:
                raise PermissionError(f"Employees are not permitted to modify HR fields: {disallowed}")

        for k, v in vals.items():
            setattr(self, k, v)
        return True


class MockPayrollRecord:
    def __init__(self, employee_id=1, basic=50000.0, hra=15000.0, allowance=5000.0, deductions=2000.0):
        self.employee_id = employee_id
        self.basic_salary = basic
        self.hra = hra
        self.special_allowance = allowance
        self.deductions = deductions
        self.gross_salary = 0.0
        self.net_salary = 0.0
        self.compute_salary()

    def compute_salary(self):
        """Calculates Gross and Net salary matching Dayflow formula."""
        if (self.basic_salary < 0 or self.hra < 0 or self.special_allowance < 0 or self.deductions < 0):
            raise ValueError("Salary amounts cannot be negative.")
        self.gross_salary = self.basic_salary + self.hra + self.special_allowance
        self.net_salary = max(0.0, self.gross_salary - self.deductions)

    def update_salary(self, user, **kwargs):
        is_hr = (
            user._is_admin() or
            user.dayflow_role == 'hr' or
            user.has_group('dayflow.group_dayflow_hr')
        )
        if not is_hr:
            raise PermissionError("Only HR can update salary structures.")

        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, float(v))
        self.compute_salary()


class TestEmployeeProfileRBAC(unittest.TestCase):

    def setUp(self):
        self.emp_user = MockUser(user_id=2, role='employee')
        self.hr_user = MockUser(user_id=1, role='hr')
        self.employee = MockEmployeeRecord(emp_id=2, name='Alex Johnson', user=self.emp_user)

    def test_employee_can_edit_permitted_fields(self):
        """Employee can update phone, address, and profile photo."""
        vals = {
            'phone': '+91 99999 88888',
            'address': 'New Residence, Bengaluru',
            'image_1920': 'base64image...'
        }
        res = self.employee.update_permitted_profile(self.emp_user, vals)
        self.assertTrue(res)
        self.assertEqual(self.employee.phone, '+91 99999 88888')
        self.assertEqual(self.employee.address, 'New Residence, Bengaluru')

    def test_employee_cannot_edit_job_title(self):
        """Employee cannot change their own job title."""
        with self.assertRaises(PermissionError):
            self.employee.update_permitted_profile(self.emp_user, {'job_title': 'VP of Engineering'})

    def test_employee_cannot_edit_department(self):
        """Employee cannot change their department."""
        with self.assertRaises(PermissionError):
            self.employee.update_permitted_profile(self.emp_user, {'department_name': 'Executive'})

    def test_employee_cannot_edit_status(self):
        """Employee cannot alter employment status."""
        with self.assertRaises(PermissionError):
            self.employee.update_permitted_profile(self.emp_user, {'status': 'inactive'})

    def test_hr_can_edit_all_fields(self):
        """HR Officer can edit job title, department, status, and personal details."""
        vals = {
            'phone': '+91 77777 66666',
            'job_title': 'Lead Architect',
            'department_name': 'Core Platform',
            'status': 'active'
        }
        res = self.employee.update_permitted_profile(self.hr_user, vals)
        self.assertTrue(res)
        self.assertEqual(self.employee.job_title, 'Lead Architect')
        self.assertEqual(self.employee.department_name, 'Core Platform')


class TestPayrollComputationAndPermissions(unittest.TestCase):

    def setUp(self):
        self.emp_user = MockUser(user_id=2, role='employee')
        self.hr_user = MockUser(user_id=1, role='hr')
        self.payroll = MockPayrollRecord(employee_id=2, basic=50000.0, hra=15000.0, allowance=5000.0, deductions=2000.0)

    def test_salary_computation(self):
        """Gross = Basic + HRA + Allowance, Net = Gross - Deductions."""
        self.assertEqual(self.payroll.gross_salary, 70000.0)
        self.assertEqual(self.payroll.net_salary, 68000.0)

    def test_negative_salary_rejected(self):
        """Negative salary components raise validation error."""
        with self.assertRaises(ValueError):
            MockPayrollRecord(employee_id=2, basic=-1000.0)

    def test_employee_cannot_update_salary(self):
        """Regular employee is denied permission to update salary."""
        with self.assertRaises(PermissionError):
            self.payroll.update_salary(self.emp_user, basic_salary=90000.0)

    def test_hr_can_update_salary_and_recalculates(self):
        """HR can update salary, automatically updating Gross and Net."""
        self.payroll.update_salary(
            self.hr_user,
            basic_salary=60000.0,
            hra=18000.0,
            special_allowance=6000.0,
            deductions=4000.0
        )
        self.assertEqual(self.payroll.gross_salary, 84000.0)
        self.assertEqual(self.payroll.net_salary, 80000.0)

    def test_deductions_exceeding_gross_net_is_zero(self):
        """Net salary cannot be negative even if deductions exceed gross."""
        self.payroll.update_salary(self.hr_user, basic_salary=1000.0, hra=0.0, special_allowance=0.0, deductions=5000.0)
        self.assertEqual(self.payroll.net_salary, 0.0)


if __name__ == '__main__':
    unittest.main()
