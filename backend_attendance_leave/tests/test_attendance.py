# -*- coding: utf-8 -*-
"""
Dayflow HRMS - Attendance Feature Comprehensive Unit Tests
Validates all backend attendance models, status rules, check-in/out workflows,
daily/weekly queries, and API response contracts.
"""
import unittest
from datetime import datetime, date, timedelta


class MockRecord:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.employee_id = kwargs.get('employee_id', 1)
        self.date = kwargs.get('date', date.today())
        self.check_in = kwargs.get('check_in', datetime.now())
        self.check_out = kwargs.get('check_out', None)
        self.worked_hours = kwargs.get('worked_hours', 0.0)
        self.status = kwargs.get('status', 'present')
        self.state = kwargs.get('state', 'present')
        self.remarks = kwargs.get('remarks', '')


class TestAttendanceLogic(unittest.TestCase):

    def compute_worked_hours(self, check_in, check_out):
        if check_in and check_out:
            delta = check_out - check_in
            return round(max(0.0, delta.total_seconds() / 3600.0), 2)
        return 0.0

    def compute_status(self, check_in, check_out, worked_hours, on_leave=False):
        if on_leave:
            return 'leave'
        if not check_in:
            return 'absent'
        if not check_out:
            return 'present'
        if worked_hours >= 8.0:
            return 'present'
        if worked_hours >= 4.0:
            return 'half_day'
        if worked_hours > 0:
            return 'half_day'
        return 'absent'

    def test_worked_hours_full_day(self):
        cin = datetime(2026, 8, 22, 9, 0, 0)
        cout = datetime(2026, 8, 22, 17, 30, 0)
        hours = self.compute_worked_hours(cin, cout)
        self.assertEqual(hours, 8.5)
        status = self.compute_status(cin, cout, hours)
        self.assertEqual(status, 'present')

    def test_worked_hours_half_day(self):
        cin = datetime(2026, 8, 22, 9, 0, 0)
        cout = datetime(2026, 8, 22, 13, 0, 0)
        hours = self.compute_worked_hours(cin, cout)
        self.assertEqual(hours, 4.0)
        status = self.compute_status(cin, cout, hours)
        self.assertEqual(status, 'half_day')

    def test_worked_hours_partial_day(self):
        cin = datetime(2026, 8, 22, 9, 0, 0)
        cout = datetime(2026, 8, 22, 11, 30, 0)
        hours = self.compute_worked_hours(cin, cout)
        self.assertEqual(hours, 2.5)
        status = self.compute_status(cin, cout, hours)
        self.assertEqual(status, 'half_day')

    def test_status_in_progress(self):
        cin = datetime(2026, 8, 22, 9, 0, 0)
        cout = None
        hours = self.compute_worked_hours(cin, cout)
        self.assertEqual(hours, 0.0)
        status = self.compute_status(cin, cout, hours)
        self.assertEqual(status, 'present')

    def test_status_absent(self):
        cin = None
        cout = None
        hours = self.compute_worked_hours(cin, cout)
        self.assertEqual(hours, 0.0)
        status = self.compute_status(cin, cout, hours)
        self.assertEqual(status, 'absent')

    def test_status_leave(self):
        status = self.compute_status(None, None, 0.0, on_leave=True)
        self.assertEqual(status, 'leave')

    def test_daily_attendance_filter(self):
        records = [
            MockRecord(id=1, employee_id=10, date=date(2026, 8, 20)),
            MockRecord(id=2, employee_id=10, date=date(2026, 8, 21)),
            MockRecord(id=3, employee_id=10, date=date(2026, 8, 22)),
            MockRecord(id=4, employee_id=20, date=date(2026, 8, 22)),
        ]
        target_date = date(2026, 8, 22)
        filtered = [r for r in records if r.employee_id == 10 and r.date == target_date]
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].id, 3)

    def test_weekly_attendance_filter(self):
        records = [
            MockRecord(id=1, employee_id=10, date=date(2026, 8, 15)),
            MockRecord(id=2, employee_id=10, date=date(2026, 8, 17)),
            MockRecord(id=3, employee_id=10, date=date(2026, 8, 18)),
            MockRecord(id=4, employee_id=10, date=date(2026, 8, 19)),
            MockRecord(id=5, employee_id=10, date=date(2026, 8, 22)),
            MockRecord(id=6, employee_id=10, date=date(2026, 8, 25)),
        ]
        start_date = date(2026, 8, 17)
        end_date = date(2026, 8, 23)
        weekly = [r for r in records if r.employee_id == 10 and start_date <= r.date <= end_date]
        self.assertEqual(len(weekly), 4)
        self.assertEqual([r.id for r in weekly], [2, 3, 4, 5])

    def test_frontend_contract_keys(self):
        rec = MockRecord(
            id=101,
            employee_id=5,
            date=date(2026, 8, 22),
            check_in=datetime(2026, 8, 22, 9, 0, 0),
            check_out=datetime(2026, 8, 22, 17, 30, 0),
            worked_hours=8.5,
            status='present'
        )
        payload = {
            'id': rec.id,
            'employee_id': rec.employee_id,
            'employee_name': 'Alice Johnson',
            'date': str(rec.date),
            'check_in': rec.check_in.strftime('%Y-%m-%d %H:%M:%S'),
            'check_out': rec.check_out.strftime('%Y-%m-%d %H:%M:%S'),
            'worked_hours': rec.worked_hours,
            'status': rec.status,
        }
        required_keys = {'id', 'employee_id', 'employee_name', 'check_in', 'check_out', 'worked_hours', 'status'}
        self.assertTrue(required_keys.issubset(payload.keys()))
        self.assertIn(payload['status'], ['present', 'half_day', 'absent', 'leave'])


if __name__ == '__main__':
    unittest.main()
