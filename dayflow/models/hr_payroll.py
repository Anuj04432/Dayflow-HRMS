# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DayflowPayroll(models.Model):
    _name = 'dayflow.payroll'
    _description = 'Dayflow Employee Salary & Payroll'
    _order = 'create_date desc'

    employee_id = fields.Many2one('dayflow.employee', string='Employee', required=True, ondelete='cascade', index=True)
    basic_salary = fields.Float(string='Basic Salary', required=True, default=0.0)
    hra = fields.Float(string='House Rent Allowance (HRA)', default=0.0)
    special_allowance = fields.Float(string='Special Allowance', default=0.0)
    deductions = fields.Float(string='Total Deductions (Tax / PF)', default=0.0)
    
    gross_salary = fields.Float(string='Gross Salary', compute='_compute_salary', store=True)
    net_salary = fields.Float(string='Net Take-Home Salary', compute='_compute_salary', store=True)
    
    payment_frequency = fields.Selection(
        [('monthly', 'Monthly'), ('bi_weekly', 'Bi-Weekly'), ('weekly', 'Weekly')],
        string='Payment Frequency',
        default='monthly',
        required=True
    )
    last_updated = fields.Datetime(string='Last Updated', default=fields.Datetime.now)

    @api.constrains('basic_salary', 'hra', 'special_allowance', 'deductions')
    def _check_salary_values(self):
        for rec in self:
            if (rec.basic_salary or 0.0) < 0 or (rec.hra or 0.0) < 0 or (rec.special_allowance or 0.0) < 0 or (rec.deductions or 0.0) < 0:
                raise exceptions.ValidationError("Salary amounts and deductions cannot be negative.")

    @api.depends('basic_salary', 'hra', 'special_allowance', 'deductions')
    def _compute_salary(self):
        for rec in self:
            rec.gross_salary = (rec.basic_salary or 0.0) + (rec.hra or 0.0) + (rec.special_allowance or 0.0)
            rec.net_salary = max(0.0, rec.gross_salary - (rec.deductions or 0.0))
