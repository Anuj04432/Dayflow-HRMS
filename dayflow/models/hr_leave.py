# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


class DayflowLeave(models.Model):
    _name = 'dayflow.leave'
    _description = 'Dayflow Leave Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    employee_id = fields.Many2one('dayflow.employee', string='Employee', required=True, ondelete='cascade', index=True)
    leave_type = fields.Selection(
        [('paid', 'Paid Leave'), ('sick', 'Sick Leave'), ('unpaid', 'Unpaid Leave')],
        string='Leave Type',
        default='paid',
        required=True,
        tracking=True
    )
    date_from = fields.Date(string='Start Date', required=True, tracking=True)
    date_to = fields.Date(string='End Date', required=True, tracking=True)
    duration_days = fields.Float(string='Duration (Days)', compute='_compute_duration', store=True)
    remarks = fields.Text(string='Employee Remarks / Reason', required=True)
    
    state = fields.Selection(
        [('pending', 'Pending Approval'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        string='Approval Status',
        default='pending',
        required=True,
        tracking=True
    )
    approved_by = fields.Many2one('res.users', string='Approved / Reviewed By', readonly=True)
    manager_remarks = fields.Text(string='Manager / HR Comments', tracking=True)

    @api.constrains('date_from', 'date_to')
    def _check_validity_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise exceptions.ValidationError("Leave end date cannot be earlier than start date.")

    @api.depends('date_from', 'date_to')
    def _compute_duration(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                if rec.date_to < rec.date_from:
                    rec.duration_days = 0.0
                else:
                    rec.duration_days = (rec.date_to - rec.date_from).days + 1
            else:
                rec.duration_days = 0.0

    def action_approve(self, comments=None):
        """Approve leave request (HR only)."""
        for rec in self:
            vals = {
                'state': 'approved',
                'approved_by': self.env.user.id,
            }
            if comments:
                vals['manager_remarks'] = comments
            rec.write(vals)
        return True

    def action_reject(self, comments=None):
        """Reject leave request (HR only)."""
        for rec in self:
            vals = {
                'state': 'rejected',
                'approved_by': self.env.user.id,
            }
            if comments:
                vals['manager_remarks'] = comments
            rec.write(vals)
        return True
