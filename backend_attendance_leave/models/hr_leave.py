# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta
from odoo import models, fields, api, exceptions


class DayflowLeave(models.Model):
    _name = 'dayflow.leave'
    _description = 'Dayflow Leave Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    employee_id = fields.Many2one(
        'dayflow.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True
    )
    leave_type = fields.Selection(
        selection=[
            ('paid', 'Paid'),
            ('sick', 'Sick'),
            ('unpaid', 'Unpaid'),
        ],
        string='Leave Type',
        default='paid',
        required=True,
        index=True,
        tracking=True,
        help='Category of leave requested: Paid, Sick, or Unpaid.'
    )
    date_from = fields.Date(
        string='Start Date',
        required=True,
        index=True,
        tracking=True
    )
    date_to = fields.Date(
        string='End Date',
        required=True,
        index=True,
        tracking=True
    )
    request_date_from = fields.Date(
        string='Request Start Date',
        compute='_compute_date_aliases',
        inverse='_inverse_date_from_alias',
        store=True
    )
    request_date_to = fields.Date(
        string='Request End Date',
        compute='_compute_date_aliases',
        inverse='_inverse_date_to_alias',
        store=True
    )
    duration_days = fields.Float(
        string='Duration (Days)',
        compute='_compute_duration',
        store=True
    )
    number_of_days = fields.Float(
        string='Number of Days',
        compute='_compute_duration',
        store=True
    )
    remarks = fields.Text(
        string='Employee Remarks / Reason',
        required=True
    )
    name = fields.Char(
        string='Description / Reason',
        compute='_compute_name_alias',
        inverse='_inverse_name_alias',
        store=True
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Approval Status',
        default='pending',
        required=True,
        index=True,
        tracking=True,
        help='State lifecycle: Draft, Pending, Approved, or Rejected.'
    )
    approved_by = fields.Many2one(
        'res.users',
        string='Approved / Reviewed By',
        readonly=True
    )
    manager_remarks = fields.Text(
        string='Manager / HR Comments',
        tracking=True
    )
    hr_comments = fields.Text(
        string='HR Comments',
        compute='_compute_hr_comments_alias',
        inverse='_inverse_hr_comments_alias',
        store=True
    )

    _sql_constraints = [
        ('date_check', 'CHECK(date_to >= date_from)', 'End date must be greater than or equal to start date!')
    ]

    @api.constrains('date_from', 'date_to')
    def _check_dates_validity(self):
        """Validate that end date is not prior to start date."""
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise exceptions.ValidationError("End date cannot be earlier than start date.")

    @api.depends('date_from', 'date_to')
    def _compute_duration(self):
        """Calculate number of leave days inclusive of start and end dates."""
        for rec in self:
            if rec.date_from and rec.date_to:
                if rec.date_to < rec.date_from:
                    rec.duration_days = 0.0
                    rec.number_of_days = 0.0
                else:
                    days = (rec.date_to - rec.date_from).days + 1
                    rec.duration_days = float(days)
                    rec.number_of_days = float(days)
            else:
                rec.duration_days = 0.0
                rec.number_of_days = 0.0

    @api.depends('date_from', 'date_to')
    def _compute_date_aliases(self):
        for rec in self:
            rec.request_date_from = rec.date_from
            rec.request_date_to = rec.date_to

    def _inverse_date_from_alias(self):
        for rec in self:
            if rec.request_date_from:
                rec.date_from = rec.request_date_from

    def _inverse_date_to_alias(self):
        for rec in self:
            if rec.request_date_to:
                rec.date_to = rec.request_date_to

    @api.depends('remarks')
    def _compute_name_alias(self):
        for rec in self:
            rec.name = rec.remarks or ''

    def _inverse_name_alias(self):
        for rec in self:
            if rec.name and not rec.remarks:
                rec.remarks = rec.name

    @api.depends('manager_remarks')
    def _compute_hr_comments_alias(self):
        for rec in self:
            rec.hr_comments = rec.manager_remarks or ''

    def _inverse_hr_comments_alias(self):
        for rec in self:
            if rec.hr_comments:
                rec.manager_remarks = rec.hr_comments

    @api.model
    def action_apply_leave(self, employee_id, leave_type, date_from, date_to, remarks):
        """
        Create a new leave request in 'pending' state after validating inputs.
        """
        if not employee_id:
            raise exceptions.ValidationError("Employee ID is required.")
        if not leave_type or leave_type not in ('paid', 'sick', 'unpaid'):
            raise exceptions.ValidationError("Invalid leave type. Must be Paid, Sick, or Unpaid.")
        if not date_from or not date_to:
            raise exceptions.ValidationError("Both start date and end date are required.")
        if not remarks or not remarks.strip():
            raise exceptions.ValidationError("Remarks / Reason is required.")

        d_from = fields.Date.from_string(date_from) if isinstance(date_from, str) else date_from
        d_to = fields.Date.from_string(date_to) if isinstance(date_to, str) else date_to

        if d_to < d_from:
            raise exceptions.ValidationError("End date cannot be earlier than start date.")

        record = self.create({
            'employee_id': employee_id,
            'leave_type': leave_type,
            'date_from': d_from,
            'date_to': d_to,
            'remarks': remarks.strip(),
            'state': 'pending',
        })
        return record

    def _is_user_hr_or_admin(self):
        """Check whether the active environment user has HR or Admin privileges."""
        user = self.env.user
        return (
            user.id == 1 or
            user.has_group('dayflow.group_dayflow_hr') or
            user.has_group('backend_attendance_leave.group_dayflow_hr')
        )

    def action_approve(self, comments=None):
        """
        Approve leave request (HR / Admin only).
        Validates that user is authorized, record is currently in 'pending' state,
        records reviewer ID and stores HR comments.
        """
        if not self._is_user_hr_or_admin():
            raise exceptions.AccessError("Only HR Officers / Admins can approve leave requests.")

        for rec in self:
            if rec.state != 'pending':
                raise exceptions.ValidationError(
                    f"Cannot approve leave request in '{rec.state}' state. Only pending requests can be approved."
                )
            rec.write({
                'state': 'approved',
                'approved_by': self.env.user.id,
                'manager_remarks': comments or rec.manager_remarks or '',
                'hr_comments': comments or rec.hr_comments or '',
            })
            # Synchronize any existing attendance records covering this date range
            try:
                attendances = self.env['dayflow.attendance'].sudo().search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('date', '>=', rec.date_from),
                    ('date', '<=', rec.date_to),
                ])
                if attendances:
                    attendances.write({'status': 'leave'})
            except Exception:
                pass
        return True

    def action_reject(self, comments=None):
        """
        Reject leave request (HR / Admin only).
        Requires HR comments explaining the reason, validates that record is currently
        in 'pending' state, and records reviewer ID.
        """
        if not self._is_user_hr_or_admin():
            raise exceptions.AccessError("Only HR Officers / Admins can reject leave requests.")

        if not comments or not comments.strip():
            raise exceptions.ValidationError("HR comments explaining the reason for rejection are required.")

        for rec in self:
            if rec.state != 'pending':
                raise exceptions.ValidationError(
                    f"Cannot reject leave request in '{rec.state}' state. Only pending requests can be rejected."
                )
            rec.write({
                'state': 'rejected',
                'approved_by': self.env.user.id,
                'manager_remarks': comments.strip(),
                'hr_comments': comments.strip(),
            })
        return True
