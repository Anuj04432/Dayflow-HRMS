# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


class DayflowEmployee(models.Model):
    _name = 'dayflow.employee'
    _description = 'Dayflow Employee Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(string='Full Name', required=True, tracking=True)
    employee_code = fields.Char(
        string='Employee ID / Code',
        required=True,
        copy=False,
        index=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('dayflow.employee.code') or 'EMP001'
    )
    user_id = fields.Many2one('res.users', string='Related User', ondelete='cascade', index=True)
    work_email = fields.Char(string='Work Email', required=True, tracking=True)
    phone = fields.Char(string='Phone Number', tracking=True)
    address = fields.Text(string='Residential Address')
    job_title = fields.Char(string='Job Title', tracking=True, default='Software Engineer')
    department_name = fields.Char(string='Department', default='Engineering')
    image_1920 = fields.Binary(string='Profile Photo')
    join_date = fields.Date(string='Joining Date', default=fields.Date.today)
    status = fields.Selection(
        [('active', 'Active'), ('on_leave', 'On Leave'), ('inactive', 'Inactive')],
        string='Status',
        default='active',
        tracking=True
    )

    # Relational fields
    attendance_ids = fields.One2many('dayflow.attendance', 'employee_id', string='Attendance Records')
    leave_ids = fields.One2many('dayflow.leave', 'employee_id', string='Leave Requests')
    payroll_ids = fields.One2many('dayflow.payroll', 'employee_id', string='Payroll Information')

    _sql_constraints = [
        ('employee_code_unique', 'unique(employee_code)', 'The Employee ID must be unique!'),
        ('work_email_unique', 'unique(work_email)', 'The Work Email must be unique!'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('employee_code') or vals.get('employee_code') == 'DF0001':
                seq_code = self.env['ir.sequence'].next_by_code('dayflow.employee.code')
                if seq_code:
                    vals['employee_code'] = seq_code
                elif not vals.get('employee_code'):
                    last_emp = self.search([], order='id desc', limit=1)
                    next_id = (last_emp.id + 1) if last_emp else 1
                    vals['employee_code'] = f"DF{next_id:04d}"
        return super(DayflowEmployee, self).create(vals_list)

    def update_permitted_profile(self, vals):
        """
        Allow regular employees to edit only permitted fields (phone, address, photo).
        HR / Admin can update all fields.
        """
        self.ensure_one()
        if not vals:
            return True

        user = self.env.user
        is_hr = (
            getattr(user, '_is_admin', None) and user._is_admin() or
            user.id == 1 or
            user.login == 'admin' or
            getattr(user, 'dayflow_role', None) == 'hr' or
            user.has_group('dayflow.group_dayflow_hr') or
            user.has_group('base.group_system')
        )
        
        if not is_hr:
            allowed_fields = {'phone', 'address', 'image_1920'}
            attempted_fields = set(vals.keys())
            disallowed = attempted_fields - allowed_fields
            if disallowed:
                raise exceptions.AccessError(
                    f"Employees are not permitted to modify HR-controlled fields: {', '.join(disallowed)}"
                )
        return self.write(vals)
