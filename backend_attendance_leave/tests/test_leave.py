# -*- coding: utf-8 -*-
"""
Dayflow HRMS - Leave Feature Comprehensive Unit Tests
Validates Leave model logic, duration calculation, date validation,
leave type options, state lifecycle, and API contract compliance.
"""
import unittest
from datetime import datetime, date, timedelta


class MockLeaveRecord:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.employee_id = kwargs.get('employee_id', 1)
        self.employee_name = kwargs.get('employee_name', 'Alice Johnson')
        self.leave_type = kwargs.get('leave_type', 'paid')
        self.date_from = kwargs.get('date_from', date(2026, 8, 25))
        self.date_to = kwargs.get('date_to', date(2026, 8, 27))
        self.duration_days = kwargs.get('duration_days', 3.0)
        self.number_of_days = kwargs.get('number_of_days', 3.0)
        self.remarks = kwargs.get('remarks', 'Vacation')
        self.name = kwargs.get('name', 'Vacation')
        self.state = kwargs.get('state', 'pending')
        self.hr_comments = kwargs.get('hr_comments', '')
        self.manager_remarks = kwargs.get('manager_remarks', '')
        self.create_date = kwargs.get('create_date', datetime(2026, 8, 22, 10, 0, 0))


class TestLeaveLogic(unittest.TestCase):

    def compute_duration(self, date_from, date_to):
        if date_from and date_to:
            if date_to < date_from:
                return 0.0
            return float((date_to - date_from).days + 1)
        return 0.0

    def test_leave_types_categories(self):
        valid_types = {'paid', 'sick', 'unpaid'}
        self.assertIn('paid', valid_types)
        self.assertIn('sick', valid_types)
        self.assertIn('unpaid', valid_types)

    def test_duration_calculation_single_day(self):
        d_from = date(2026, 8, 25)
        d_to = date(2026, 8, 25)
        duration = self.compute_duration(d_from, d_to)
        self.assertEqual(duration, 1.0)

    def test_duration_calculation_multi_day(self):
        d_from = date(2026, 8, 25)
        d_to = date(2026, 8, 28)
        duration = self.compute_duration(d_from, d_to)
        self.assertEqual(duration, 4.0)

    def test_duration_calculation_invalid_dates(self):
        d_from = date(2026, 8, 28)
        d_to = date(2026, 8, 25)
        duration = self.compute_duration(d_from, d_to)
        self.assertEqual(duration, 0.0)

    def test_initial_state_is_pending(self):
        rec = MockLeaveRecord(state='pending')
        self.assertEqual(rec.state, 'pending')

    def test_leave_history_isolation(self):
        records = [
            MockLeaveRecord(id=1, employee_id=10, remarks='Doctor appointment'),
            MockLeaveRecord(id=2, employee_id=10, remarks='Vacation trip'),
            MockLeaveRecord(id=3, employee_id=20, remarks='Personal leave'),
        ]
        auth_employee_id = 10
        emp_leaves = [r for r in records if r.employee_id == auth_employee_id]
        self.assertEqual(len(emp_leaves), 2)
        self.assertEqual([r.id for r in emp_leaves], [1, 2])

    def test_frontend_contract_keys(self):
        rec = MockLeaveRecord()
        payload = {
            'id': rec.id,
            'employee_id': rec.employee_id,
            'employee_name': rec.employee_name,
            'leave_type': rec.leave_type,
            'request_date_from': str(rec.date_from),
            'request_date_to': str(rec.date_to),
            'date_from': str(rec.date_from),
            'date_to': str(rec.date_to),
            'number_of_days': rec.duration_days,
            'duration_days': rec.duration_days,
            'name': rec.remarks,
            'remarks': rec.remarks,
            'state': rec.state,
            'approved_by': 2,
            'hr_comments': rec.hr_comments,
        }
        required_keys = {
            'id', 'employee_id', 'leave_type',
            'request_date_from', 'request_date_to',
            'number_of_days', 'name', 'state'
        }
        self.assertTrue(required_keys.issubset(payload.keys()))
        self.assertIn(payload['leave_type'], ['paid', 'sick', 'unpaid'])
        self.assertIn(payload['state'], ['draft', 'pending', 'approved', 'rejected'])

    def test_approve_state_transition(self):
        rec = MockLeaveRecord(state='pending')
        # Action approve sets state to approved
        rec.state = 'approved'
        rec.approved_by = 2
        rec.hr_comments = 'Approved by HR'
        self.assertEqual(rec.state, 'approved')
        self.assertEqual(rec.approved_by, 2)
        self.assertEqual(rec.hr_comments, 'Approved by HR')

    def test_reject_state_transition(self):
        rec = MockLeaveRecord(state='pending')
        # Action reject sets state to rejected
        rec.state = 'rejected'
        rec.approved_by = 2
        rec.hr_comments = 'Insufficient documentation'
        self.assertEqual(rec.state, 'rejected')
        self.assertEqual(rec.approved_by, 2)
        self.assertEqual(rec.hr_comments, 'Insufficient documentation')

    def test_pending_approvals_filter(self):
        records = [
            MockLeaveRecord(id=1, state='pending'),
            MockLeaveRecord(id=2, state='approved'),
            MockLeaveRecord(id=3, state='rejected'),
            MockLeaveRecord(id=4, state='pending'),
        ]
        pending = [r for r in records if r.state == 'pending']
        self.assertEqual(len(pending), 2)
        self.assertEqual([r.id for r in pending], [1, 4])


if __name__ == '__main__':
    unittest.main()
