# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta
from odoo import models, fields, api, exceptions


class DayflowAttendance(models.Model):
    _name = 'dayflow.attendance'
    _description = 'Dayflow Attendance Record'
    _order = 'check_in desc, id desc'

    employee_id = fields.Many2one(
        'dayflow.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True
    )
    date = fields.Date(
        string='Date',
        default=fields.Date.today,
        index=True,
        required=True
    )
    check_in = fields.Datetime(
        string='Check In',
        required=True,
        default=fields.Datetime.now,
        index=True
    )
    check_out = fields.Datetime(
        string='Check Out',
        index=True
    )
    worked_hours = fields.Float(
        string='Worked Hours',
        compute='_compute_worked_hours',
        store=True,
        digits=(16, 2)
    )
    status = fields.Selection(
        selection=[
            ('present', 'Present'),
            ('half_day', 'Half-day'),
            ('absent', 'Absent'),
            ('leave', 'Leave'),
        ],
        string='Status',
        compute='_compute_status',
        store=True,
        readonly=False,
        default='present',
        index=True,
        help='Attendance status: Present, Half-day, Absent, or Leave.'
    )
    # Backward compatibility alias for state
    state = fields.Selection(
        selection=[
            ('present', 'Present'),
            ('half_day', 'Half-day'),
            ('absent', 'Absent'),
            ('leave', 'Leave'),
        ],
        string='State',
        compute='_compute_state_alias',
        inverse='_inverse_state_alias',
        store=True
    )
    remarks = fields.Char(string='Notes')

    _sql_constraints = [
        ('check_in_out_order', 'CHECK(check_out IS NULL OR check_out >= check_in)',
         'Check-out time must be greater than or equal to check-in time!')
    ]

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """Ensure check_out is not prior to check_in."""
        for rec in self:
            if rec.check_in and rec.check_out and rec.check_out < rec.check_in:
                raise exceptions.ValidationError("Check-out time cannot be earlier than check-in time.")

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        """Compute worked hours in decimal format based on check-in and check-out."""
        for rec in self:
            if rec.check_in and rec.check_out:
                delta = rec.check_out - rec.check_in
                rec.worked_hours = round(max(0.0, delta.total_seconds() / 3600.0), 2)
            else:
                rec.worked_hours = 0.0

    @api.depends('worked_hours', 'check_in', 'check_out')
    def _compute_status(self):
        """
        Compute attendance status based on worked hours:
        - In-progress (check_in without check_out): 'present'
        - Worked >= 8.0 hours: 'present' (full day)
        - Worked >= 4.0 and < 8.0 hours: 'half_day'
        - Worked > 0 and < 4.0 hours: 'half_day' (partial attendance)
        - No check_in or 0 hours: 'absent'
        """
        for rec in self:
            if not rec.check_in:
                rec.status = 'absent'
            elif not rec.check_out:
                # Active in-progress attendance
                rec.status = 'present'
            elif rec.worked_hours >= 8.0:
                rec.status = 'present'
            elif rec.worked_hours >= 4.0:
                rec.status = 'half_day'
            elif rec.worked_hours > 0:
                rec.status = 'half_day'
            else:
                rec.status = 'absent'

    @api.depends('status')
    def _compute_state_alias(self):
        for rec in self:
            rec.state = rec.status

    def _inverse_state_alias(self):
        for rec in self:
            if rec.state:
                rec.status = rec.state

    @api.model
    def action_check_in(self, employee_id):
        """
        Initiate check-in for the given employee.
        Validates that no open attendance record already exists.
        """
        if not employee_id:
            raise exceptions.ValidationError("Employee ID is required for check-in.")

        open_attendance = self.search([
            ('employee_id', '=', employee_id),
            ('check_out', '=', False)
        ], limit=1)

        if open_attendance:
            raise exceptions.ValidationError(
                "Employee is already checked in. Please check out before checking in again."
            )

        now = fields.Datetime.now()
        today = fields.Date.today()
        record = self.create({
            'employee_id': employee_id,
            'date': today,
            'check_in': now,
            'status': 'present',
        })
        return record

    @api.model
    def action_check_out(self, employee_id):
        """
        Complete check-out for the given employee's active attendance.
        Updates check_out timestamp and recomputes worked hours and status.
        """
        if not employee_id:
            raise exceptions.ValidationError("Employee ID is required for check-out.")

        open_attendance = self.search([
            ('employee_id', '=', employee_id),
            ('check_out', '=', False)
        ], order='check_in desc, id desc', limit=1)

        if not open_attendance:
            raise exceptions.ValidationError(
                "No active check-in found for this employee. Please check in first."
            )

        now = fields.Datetime.now()
        open_attendance.write({
            'check_out': now
        })
        return open_attendance

    @api.model
    def get_daily_attendance(self, employee_id, target_date=None):
        """
        Retrieve daily attendance records for a specific employee and date.
        """
        query_date = target_date or fields.Date.today()
        return self.search([
            ('employee_id', '=', employee_id),
            ('date', '=', query_date)
        ], order='check_in desc')

    @api.model
    def get_weekly_attendance(self, employee_id, start_date=None, end_date=None):
        """
        Retrieve attendance records for a specific employee over a weekly date range.
        If start_date is not provided, defaults to the current week's start (Monday).
        """
        if not start_date:
            today = fields.Date.today()
            start_date = today - timedelta(days=today.weekday())
        
        if not end_date:
            if isinstance(start_date, str):
                start_dt = fields.Date.from_string(start_date)
            else:
                start_dt = start_date
            end_date = start_dt + timedelta(days=6)

        return self.search([
            ('employee_id', '=', employee_id),
            ('date', '>=', start_date),
            ('date', '<=', end_date)
        ], order='date asc, check_in asc')
