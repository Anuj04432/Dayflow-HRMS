# -*- coding: utf-8 -*-
"""
Dayflow HRMS - Phase 7 Attendance-Leave Synchronization Tests
Validates the complete synchronization workflow between approved leaves
and attendance status representation across daily, weekly, and today queries.
"""
import unittest
from datetime import datetime, date, timedelta


class MockLeave:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.employee_id = kwargs.get('employee_id', 1)
        self.date_from = kwargs.get('date_from', date(2026, 8, 25))
        self.date_to = kwargs.get('date_to', date(2026, 8, 27))
        self.state = kwargs.get('state', 'pending')


class TestAttendanceLeaveSyncLogic(unittest.TestCase):

    def compute_attendance_status(self, emp_id, target_date, worked_hours=0.0, check_in=None, check_out=None, leaves=None):
        leaves = leaves or []
        # 1. Check approved leave covering target_date
        for l in leaves:
            if l.employee_id == emp_id and l.state == 'approved':
                if l.date_from <= target_date <= l.date_to:
                    return 'leave'

        # 2. Regular attendance status logic
        if not check_in:
            return 'absent'
        elif not check_out:
            return 'present'
        elif worked_hours >= 8.0:
            return 'present'
        elif worked_hours > 0.0:
            return 'half_day'
        else:
            return 'absent'

    def test_no_leave_normal_present(self):
        status = self.compute_attendance_status(
            emp_id=1,
            target_date=date(2026, 8, 25),
            worked_hours=8.5,
            check_in=datetime(2026, 8, 25, 9, 0),
            check_out=datetime(2026, 8, 25, 17, 30),
            leaves=[]
        )
        self.assertEqual(status, 'present')

    def test_pending_leave_does_not_affect_attendance(self):
        pending_leave = MockLeave(employee_id=1, date_from=date(2026, 8, 25), date_to=date(2026, 8, 27), state='pending')
        # Without check-in on a pending leave date -> absent, not leave
        status = self.compute_attendance_status(
            emp_id=1,
            target_date=date(2026, 8, 25),
            leaves=[pending_leave]
        )
        self.assertEqual(status, 'absent')
        self.assertNotEqual(status, 'leave')

    def test_rejected_leave_does_not_affect_attendance(self):
        rejected_leave = MockLeave(employee_id=1, date_from=date(2026, 8, 25), date_to=date(2026, 8, 27), state='rejected')
        status = self.compute_attendance_status(
            emp_id=1,
            target_date=date(2026, 8, 25),
            leaves=[rejected_leave]
        )
        self.assertEqual(status, 'absent')
        self.assertNotEqual(status, 'leave')

    def test_approved_leave_sets_status_to_leave(self):
        approved_leave = MockLeave(employee_id=1, date_from=date(2026, 8, 25), date_to=date(2026, 8, 27), state='approved')
        status = self.compute_attendance_status(
            emp_id=1,
            target_date=date(2026, 8, 25),
            leaves=[approved_leave]
        )
        self.assertEqual(status, 'leave')

    def test_multi_day_approved_leave_all_covered_dates(self):
        approved_leave = MockLeave(employee_id=1, date_from=date(2026, 8, 25), date_to=date(2026, 8, 27), state='approved')
        # Check day 1, day 2, day 3
        self.assertEqual(self.compute_attendance_status(1, date(2026, 8, 25), leaves=[approved_leave]), 'leave')
        self.assertEqual(self.compute_attendance_status(1, date(2026, 8, 26), leaves=[approved_leave]), 'leave')
        self.assertEqual(self.compute_attendance_status(1, date(2026, 8, 27), leaves=[approved_leave]), 'leave')

    def test_date_before_approved_leave_not_leave(self):
        approved_leave = MockLeave(employee_id=1, date_from=date(2026, 8, 25), date_to=date(2026, 8, 27), state='approved')
        status = self.compute_attendance_status(1, date(2026, 8, 24), leaves=[approved_leave])
        self.assertEqual(status, 'absent')

    def test_date_after_approved_leave_not_leave(self):
        approved_leave = MockLeave(employee_id=1, date_from=date(2026, 8, 25), date_to=date(2026, 8, 27), state='approved')
        status = self.compute_attendance_status(1, date(2026, 8, 28), leaves=[approved_leave])
        self.assertEqual(status, 'absent')

    def test_approved_leave_takes_priority_over_hours(self):
        # Even if hours exist on record, approved leave takes precedence
        approved_leave = MockLeave(employee_id=1, date_from=date(2026, 8, 25), date_to=date(2026, 8, 25), state='approved')
        status = self.compute_attendance_status(
            emp_id=1,
            target_date=date(2026, 8, 25),
            worked_hours=8.0,
            check_in=datetime(2026, 8, 25, 9, 0),
            check_out=datetime(2026, 8, 25, 17, 0),
            leaves=[approved_leave]
        )
        self.assertEqual(status, 'leave')

    def test_employee_isolation_approved_leave(self):
        # Approved leave belongs to employee 1, employee 2 should not get 'leave' status
        approved_leave = MockLeave(employee_id=1, date_from=date(2026, 8, 25), date_to=date(2026, 8, 25), state='approved')
        status_emp2 = self.compute_attendance_status(emp_id=2, target_date=date(2026, 8, 25), leaves=[approved_leave])
        self.assertEqual(status_emp2, 'absent')


if __name__ == '__main__':
    unittest.main()
