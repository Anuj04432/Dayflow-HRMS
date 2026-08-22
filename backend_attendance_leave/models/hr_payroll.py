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

    @api.depends('basic_salary', 'hra', 'special_allowance', 'deductions')
    def _compute_salary(self):
        for rec in self:
            rec.gross_salary = rec.basic_salary + rec.hra + rec.special_allowance
            rec.net_salary = max(0.0, rec.gross_salary - rec.deductions)
