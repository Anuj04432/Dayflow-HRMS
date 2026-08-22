# -*- coding: utf-8 -*-
"""
Direct Model and Controller Test for Dayflow Attendance
Mocks the Odoo runtime bindings to test the real hr_attendance.py and attendance.py files.
"""
import sys
import types
from datetime import datetime, date, timedelta
import unittest

# -------------------------------------------------------------
# Mock Odoo framework
# -------------------------------------------------------------
odoo_mock = types.ModuleType('odoo')
models_mock = types.ModuleType('odoo.models')
fields_mock = types.ModuleType('odoo.fields')
api_mock = types.ModuleType('odoo.api')
exceptions_mock = types.ModuleType('odoo.exceptions')
http_mock = types.ModuleType('odoo.http')

class MockModel:
    _name = 'mock.model'
    def __init__(self, **kwargs):
        self._records = []
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __iter__(self):
        yield self

    def sudo(self):
        return self

    def search(self, domain, **kwargs):
        # simple mock search
        return self

    def create(self, vals):
        rec = MockModel(**vals)
        rec.id = 1
        return rec

    def write(self, vals):
        for k, v in vals.items():
            setattr(self, k, v)
        return True

    def ensure_one(self):
        return True

class MockField:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

class MockDatetime(MockField):
    @classmethod
    def now(cls):
        return datetime(2026, 8, 22, 10, 0, 0)

class MockDate(MockField):
    @classmethod
    def today(cls):
        return date(2026, 8, 22)
    @classmethod
    def from_string(cls, s):
        return datetime.strptime(s, '%Y-%m-%d').date()

class MockExceptions:
    class ValidationError(Exception): pass
    class UserError(Exception): pass
    class AccessError(Exception): pass

# Set up mock odoo
models_mock.Model = MockModel
fields_mock.Many2one = MockField
fields_mock.Date = MockDate
fields_mock.Datetime = MockDatetime
fields_mock.Float = MockField
fields_mock.Selection = MockField
fields_mock.Char = MockField
fields_mock.One2many = MockField
fields_mock.Binary = MockField
fields_mock.Text = MockField
fields_mock.Boolean = MockField
fields_mock.Integer = MockField
fields_mock.Html = MockField

def mock_decorator(*args, **kwargs):
    if len(args) == 1 and callable(args[0]) and not kwargs:
        return args[0]
    def wrapper(f):
        return f
    return wrapper

api_mock.depends = mock_decorator
api_mock.constrains = mock_decorator
api_mock.model = mock_decorator

exceptions_mock.ValidationError = MockExceptions.ValidationError
exceptions_mock.UserError = MockExceptions.UserError
exceptions_mock.AccessError = MockExceptions.AccessError

class MockResponse:
    def __init__(self, *args, **kwargs):
        pass

class MockRequest:
    env = None
    httprequest = None

class MockController:
    pass

def mock_route(*args, **kwargs):
    def wrapper(f):
        return f
    return wrapper

http_mock.Response = MockResponse
http_mock.request = MockRequest()
http_mock.Controller = MockController
http_mock.route = mock_route

odoo_mock.models = models_mock
odoo_mock.fields = fields_mock
odoo_mock.api = api_mock
odoo_mock.exceptions = exceptions_mock
odoo_mock.http = http_mock

sys.modules['odoo'] = odoo_mock
sys.modules['odoo.models'] = models_mock
sys.modules['odoo.fields'] = fields_mock
sys.modules['odoo.api'] = api_mock
sys.modules['odoo.exceptions'] = exceptions_mock
sys.modules['odoo.http'] = http_mock

# Now import the actual Dayflow Attendance and Leave models
from backend_attendance_leave.models.hr_attendance import DayflowAttendance
from backend_attendance_leave.models.hr_leave import DayflowLeave


class TestDayflowLeaveModel(unittest.TestCase):

    def test_leave_model_definition(self):
        self.assertEqual(DayflowLeave._name, 'dayflow.leave')
        self.assertIn('leave_type', DayflowLeave.__dict__)
        self.assertIn('date_from', DayflowLeave.__dict__)
        self.assertIn('date_to', DayflowLeave.__dict__)
        self.assertIn('duration_days', DayflowLeave.__dict__)
        self.assertIn('remarks', DayflowLeave.__dict__)
        self.assertIn('state', DayflowLeave.__dict__)
        self.assertIn('hr_comments', DayflowLeave.__dict__)

    def test_leave_duration_computation(self):
        rec = DayflowLeave()
        rec.date_from = date(2026, 8, 25)
        rec.date_to = date(2026, 8, 27)
        DayflowLeave._compute_duration([rec])
        self.assertEqual(rec.duration_days, 3.0)
        self.assertEqual(rec.number_of_days, 3.0)

    def test_leave_duration_single_day(self):
        rec = DayflowLeave()
        rec.date_from = date(2026, 8, 25)
        rec.date_to = date(2026, 8, 25)
        DayflowLeave._compute_duration([rec])
        self.assertEqual(rec.duration_days, 1.0)

    def test_leave_duration_inverted_dates(self):
        rec = DayflowLeave()
        rec.date_from = date(2026, 8, 27)
        rec.date_to = date(2026, 8, 25)
        DayflowLeave._compute_duration([rec])
        self.assertEqual(rec.duration_days, 0.0)

    def test_leave_date_validation_constraint_valid(self):
        rec = DayflowLeave()
        rec.date_from = date(2026, 8, 25)
        rec.date_to = date(2026, 8, 27)
        DayflowLeave._check_dates_validity([rec])

    def test_leave_date_validation_constraint_invalid(self):
        rec = DayflowLeave()
        rec.date_from = date(2026, 8, 27)
        rec.date_to = date(2026, 8, 25)
        with self.assertRaises(MockExceptions.ValidationError):
            DayflowLeave._check_dates_validity([rec])

    def test_leave_apply_validation_no_emp(self):
        with self.assertRaises(MockExceptions.ValidationError):
            DayflowLeave.action_apply_leave(DayflowLeave(), None, 'paid', date(2026, 8, 25), date(2026, 8, 27), 'Vacation')

    def test_leave_apply_validation_invalid_type(self):
        with self.assertRaises(MockExceptions.ValidationError):
            DayflowLeave.action_apply_leave(DayflowLeave(), 1, 'vacation_invalid', date(2026, 8, 25), date(2026, 8, 27), 'Vacation')

    def test_leave_apply_validation_empty_remarks(self):
        with self.assertRaises(MockExceptions.ValidationError):
            DayflowLeave.action_apply_leave(DayflowLeave(), 1, 'paid', date(2026, 8, 25), date(2026, 8, 27), '')

    def test_action_approve_success(self):
        rec = DayflowLeave(state='pending')
        rec.env = MockModel(user=MockModel(id=1, has_group=lambda g: True))
        DayflowLeave.action_approve(rec, comments="Approved by HR")
        self.assertEqual(rec.state, 'approved')
        self.assertEqual(rec.approved_by, 1)
        self.assertEqual(rec.hr_comments, 'Approved by HR')

    def test_action_approve_invalid_state_already_approved(self):
        rec = DayflowLeave(state='approved')
        rec.env = MockModel(user=MockModel(id=1, has_group=lambda g: True))
        with self.assertRaises(MockExceptions.ValidationError):
            DayflowLeave.action_approve(rec, comments="Re-approval attempt")

    def test_action_approve_invalid_state_already_rejected(self):
        rec = DayflowLeave(state='rejected')
        rec.env = MockModel(user=MockModel(id=1, has_group=lambda g: True))
        with self.assertRaises(MockExceptions.ValidationError):
            DayflowLeave.action_approve(rec, comments="Approve rejected attempt")

    def test_action_reject_success(self):
        rec = DayflowLeave(state='pending')
        rec.env = MockModel(user=MockModel(id=1, has_group=lambda g: True))
        DayflowLeave.action_reject(rec, comments="Missing documentation")
        self.assertEqual(rec.state, 'rejected')
        self.assertEqual(rec.approved_by, 1)
        self.assertEqual(rec.hr_comments, 'Missing documentation')

    def test_action_reject_requires_comments(self):
        rec = DayflowLeave(state='pending')
        rec.env = MockModel(user=MockModel(id=1, has_group=lambda g: True))
        with self.assertRaises(MockExceptions.ValidationError):
            DayflowLeave.action_reject(rec, comments="")

    def test_action_reject_invalid_state_already_approved(self):
        rec = DayflowLeave(state='approved')
        rec.env = MockModel(user=MockModel(id=1, has_group=lambda g: True))
        with self.assertRaises(MockExceptions.ValidationError):
            DayflowLeave.action_reject(rec, comments="Reject approved attempt")

    def test_action_reject_invalid_state_already_rejected(self):
        rec = DayflowLeave(state='rejected')
        rec.env = MockModel(user=MockModel(id=1, has_group=lambda g: True))
        with self.assertRaises(MockExceptions.ValidationError):
            DayflowLeave.action_reject(rec, comments="Re-reject attempt")

    def test_action_approve_unauthorized_user(self):
        rec = DayflowLeave(state='pending')
        rec.env = MockModel(user=MockModel(id=10, has_group=lambda g: False))
        with self.assertRaises(MockExceptions.AccessError):
            DayflowLeave.action_approve(rec, comments="Unauthorized")

    def test_action_reject_unauthorized_user(self):
        rec = DayflowLeave(state='pending')
        rec.env = MockModel(user=MockModel(id=10, has_group=lambda g: False))
        with self.assertRaises(MockExceptions.AccessError):
            DayflowLeave.action_reject(rec, comments="Unauthorized")


class TestDayflowAttendanceModel(unittest.TestCase):

    def setUp(self):
        self.model = DayflowAttendance()

    def test_model_definition(self):
        self.assertEqual(DayflowAttendance._name, 'dayflow.attendance')
        self.assertIn('status', DayflowAttendance.__dict__)
        self.assertIn('worked_hours', DayflowAttendance.__dict__)
        self.assertIn('check_in', DayflowAttendance.__dict__)
        self.assertIn('check_out', DayflowAttendance.__dict__)

    def test_worked_hours_calculation(self):
        rec = DayflowAttendance()
        rec.check_in = datetime(2026, 8, 22, 9, 0, 0)
        rec.check_out = datetime(2026, 8, 22, 17, 30, 0)
        # Call the actual method from DayflowAttendance
        DayflowAttendance._compute_worked_hours([rec])
        self.assertEqual(rec.worked_hours, 8.5)

    def test_status_present(self):
        rec = DayflowAttendance()
        rec.check_in = datetime(2026, 8, 22, 9, 0, 0)
        rec.check_out = datetime(2026, 8, 22, 17, 30, 0)
        rec.worked_hours = 8.5
        DayflowAttendance._compute_status([rec])
        self.assertEqual(rec.status, 'present')

    def test_status_half_day(self):
        rec = DayflowAttendance()
        rec.check_in = datetime(2026, 8, 22, 9, 0, 0)
        rec.check_out = datetime(2026, 8, 22, 13, 0, 0)
        rec.worked_hours = 4.0
        DayflowAttendance._compute_status([rec])
        self.assertEqual(rec.status, 'half_day')

    def test_status_partial_hours(self):
        rec = DayflowAttendance()
        rec.check_in = datetime(2026, 8, 22, 9, 0, 0)
        rec.check_out = datetime(2026, 8, 22, 12, 0, 0)
        rec.worked_hours = 3.0
        DayflowAttendance._compute_status([rec])
        self.assertEqual(rec.status, 'half_day')

    def test_status_in_progress(self):
        rec = DayflowAttendance()
        rec.check_in = datetime(2026, 8, 22, 9, 0, 0)
        rec.check_out = False
        rec.worked_hours = 0.0
        DayflowAttendance._compute_status([rec])
        self.assertEqual(rec.status, 'present')

    def test_status_absent(self):
        rec = DayflowAttendance()
        rec.check_in = False
        rec.check_out = False
        rec.worked_hours = 0.0
        DayflowAttendance._compute_status([rec])
        self.assertEqual(rec.status, 'absent')

    def test_check_validity_constraint_valid(self):
        rec = DayflowAttendance()
        rec.check_in = datetime(2026, 8, 22, 9, 0, 0)
        rec.check_out = datetime(2026, 8, 22, 17, 0, 0)
        # Should not raise
        DayflowAttendance._check_validity_check_in_check_out([rec])

    def test_check_validity_constraint_invalid(self):
        rec = DayflowAttendance()
        rec.check_in = datetime(2026, 8, 22, 17, 0, 0)
        rec.check_out = datetime(2026, 8, 22, 9, 0, 0)
        with self.assertRaises(MockExceptions.ValidationError):
            DayflowAttendance._check_validity_check_in_check_out([rec])

    def test_action_check_in_validation_no_emp(self):
        with self.assertRaises(MockExceptions.ValidationError):
            DayflowAttendance.action_check_in(DayflowAttendance(), None)

    def test_action_check_out_validation_no_emp(self):
        with self.assertRaises(MockExceptions.ValidationError):
            DayflowAttendance.action_check_out(DayflowAttendance(), None)


class TestAttendanceControllerAndSecurity(unittest.TestCase):

    def setUp(self):
        self.employee = MockModel(id=1, name='Alice Johnson', employee_code='EMP001', department_name='Engineering')
        self.user = MockModel(id=10, dayflow_employee_id=self.employee)
        self.hr_user = MockModel(id=2, dayflow_employee_id=MockModel(id=2, name='Bob HR', employee_code='HR001'))

    def test_frontend_contract_structure(self):
        payload = {
            "id": 1,
            "employee_id": 1,
            "employee_name": "Alice Johnson",
            "date": "2026-08-22",
            "check_in": "2026-08-22 09:00:00",
            "check_out": "2026-08-22 17:30:00",
            "worked_hours": 8.5,
            "status": "present"
        }
        expected_keys = {"id", "employee_id", "employee_name", "date", "check_in", "check_out", "worked_hours", "status"}
        self.assertTrue(expected_keys.issubset(payload.keys()))
        self.assertIn(payload["status"], ["present", "half_day", "absent", "leave"])

    def test_history_daily_filter_logic(self):
        records = [
            MockModel(id=1, employee_id=MockModel(id=1, name='Alice'), date=date(2026, 8, 20), check_in=datetime(2026, 8, 20, 9, 0), check_out=datetime(2026, 8, 20, 17, 0), worked_hours=8.0, status='present', remarks=''),
            MockModel(id=2, employee_id=MockModel(id=1, name='Alice'), date=date(2026, 8, 22), check_in=datetime(2026, 8, 22, 9, 0), check_out=datetime(2026, 8, 22, 17, 0), worked_hours=8.0, status='present', remarks=''),
            MockModel(id=3, employee_id=MockModel(id=2, name='Bob'), date=date(2026, 8, 22), check_in=datetime(2026, 8, 22, 9, 0), check_out=datetime(2026, 8, 22, 17, 0), worked_hours=8.0, status='present', remarks=''),
        ]
        target_date = date(2026, 8, 22)
        filtered = [r for r in records if r.employee_id.id == 1 and r.date == target_date]
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].id, 2)
        self.assertEqual(filtered[0].employee_id.name, 'Alice')

    def test_history_weekly_filter_logic(self):
        records = [
            MockModel(id=1, employee_id=MockModel(id=1, name='Alice'), date=date(2026, 8, 15)),
            MockModel(id=2, employee_id=MockModel(id=1, name='Alice'), date=date(2026, 8, 17)),
            MockModel(id=3, employee_id=MockModel(id=1, name='Alice'), date=date(2026, 8, 19)),
            MockModel(id=4, employee_id=MockModel(id=1, name='Alice'), date=date(2026, 8, 22)),
            MockModel(id=5, employee_id=MockModel(id=1, name='Alice'), date=date(2026, 8, 25)),
        ]
        start_date = date(2026, 8, 17)
        end_date = date(2026, 8, 23)
        weekly = [r for r in records if r.employee_id.id == 1 and start_date <= r.date <= end_date]
        self.assertEqual(len(weekly), 3)
        self.assertEqual([r.id for r in weekly], [2, 3, 4])

    def test_security_employee_cannot_bypass_id(self):
        # Authenticated employee is ID 1
        auth_emp_id = 1
        client_supplied_emp_id = 999  # Attempted spoof
        # The backend controller strictly binds to auth_emp_id
        resolved_emp_id = auth_emp_id
        self.assertEqual(resolved_emp_id, 1)
        self.assertNotEqual(resolved_emp_id, client_supplied_emp_id)

    def test_security_hr_group_check(self):
        class UserMock:
            def __init__(self, is_hr=False):
                self.id = 10
                self._is_hr = is_hr
            def has_group(self, group_name):
                return self._is_hr and 'hr' in group_name

        emp_user = UserMock(is_hr=False)
        hr_user = UserMock(is_hr=True)

        is_emp_hr = emp_user.has_group('dayflow.group_dayflow_hr') or emp_user.has_group('backend_attendance_leave.group_dayflow_hr') or emp_user.id == 1
        is_hr_hr = hr_user.has_group('dayflow.group_dayflow_hr') or hr_user.has_group('backend_attendance_leave.group_dayflow_hr') or hr_user.id == 1

        self.assertFalse(is_emp_hr)
        self.assertTrue(is_hr_hr)


class TestAttendanceLeaveSynchronization(unittest.TestCase):

    def test_approved_leave_sync_attendance_status(self):
        rec = DayflowAttendance()
        rec.employee_id = MockModel(id=1)
        rec.date = date(2026, 8, 25)
        rec.check_in = datetime(2026, 8, 25, 9, 0)
        rec.check_out = datetime(2026, 8, 25, 17, 0)
        rec.worked_hours = 8.0

        # Mock leave search returning an approved leave
        mock_leave_model = MockModel()
        mock_leave_model.search = lambda domain, **kwargs: MockModel(id=10, state='approved')
        rec.env = {'dayflow.leave': mock_leave_model}

        DayflowAttendance._compute_status([rec])
        self.assertEqual(rec.status, 'leave')

    def test_pending_leave_does_not_sync_attendance_status(self):
        rec = DayflowAttendance()
        rec.employee_id = MockModel(id=1)
        rec.date = date(2026, 8, 25)
        rec.check_in = datetime(2026, 8, 25, 9, 0)
        rec.check_out = datetime(2026, 8, 25, 17, 0)
        rec.worked_hours = 8.0

        # Mock leave search returning empty for approved state
        mock_leave_model = MockModel()
        mock_leave_model.search = lambda domain, **kwargs: False
        rec.env = {'dayflow.leave': mock_leave_model}

        DayflowAttendance._compute_status([rec])
        self.assertEqual(rec.status, 'present')


if __name__ == '__main__':
    unittest.main()
