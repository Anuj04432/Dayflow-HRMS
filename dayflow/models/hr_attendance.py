# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


class DayflowAttendance(models.Model):
    _name = 'dayflow.attendance'
    _description = 'Dayflow Attendance Record'
    _order = 'check_in desc'

    employee_id = fields.Many2one('dayflow.employee', string='Employee', required=True, ondelete='cascade', index=True)
    date = fields.Date(string='Date', default=fields.Date.today, index=True)
    check_in = fields.Datetime(string='Check In', required=True, default=fields.Datetime.now)
    check_out = fields.Datetime(string='Check Out')
    worked_hours = fields.Float(string='Worked Hours', compute='_compute_worked_hours', store=True)
    state = fields.Selection(
        [('present', 'Present'), ('half_day', 'Half-day'), ('absent', 'Absent'), ('leave', 'On Leave')],
        string='Status',
        default='present',
        required=True
    )
    remarks = fields.Char(string='Notes')

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                delta = rec.check_out - rec.check_in
                rec.worked_hours = round(delta.total_seconds() / 3600.0, 2)
            else:
                rec.worked_hours = 0.0
