# -*- coding: utf-8 -*-
import logging
from odoo import http, fields
from odoo.http import request
from .common import json_response, options_response, get_json_body, is_hr_user, get_auth_context

_logger = logging.getLogger(__name__)


class DayflowPayrollController(http.Controller):

    @http.route('/api/payroll/salary-info', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_salary_info(self, employee_id=None, **kwargs):
        """Retrieve employee salary structure. Employees see own read-only; HR can inspect any employee."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        user, current_employee, err = get_auth_context()
        if err:
            return err

        is_hr = is_hr_user(user)

        if employee_id and is_hr:
            try:
                emp_id_int = int(employee_id)
                employee = request.env['dayflow.employee'].sudo().browse(emp_id_int)
            except (ValueError, TypeError):
                return json_response(success=False, status=400, message='Invalid employee_id.')
        else:
            employee = current_employee

        if not employee or not employee.exists():
            return json_response(success=False, status=404, message='Employee record not found.')

        payroll = request.env['dayflow.payroll'].sudo().search([('employee_id', '=', employee.id)], limit=1)

        if not payroll:
            # Auto-create fallback structure if missing
            payroll = request.env['dayflow.payroll'].sudo().create({
                'employee_id': employee.id,
                'basic_salary': 50000.0,
                'hra': 15000.0,
                'special_allowance': 5000.0,
                'deductions': 2000.0,
            })

        last_updated_str = payroll.last_updated.strftime('%Y-%m-%d %H:%M:%S') if (payroll.last_updated and hasattr(payroll.last_updated, 'strftime')) else (str(payroll.last_updated) if payroll.last_updated else None)

        salary_data = {
            'employee_id': employee.id,
            'employee_name': employee.name,
            'employee_code': employee.employee_code,
            'job_title': employee.job_title,
            'basic_salary': payroll.basic_salary,
            'hra': payroll.hra,
            'special_allowance': payroll.special_allowance,
            'deductions': payroll.deductions,
            'gross_salary': payroll.gross_salary,
            'net_salary': payroll.net_salary,
            'payment_frequency': payroll.payment_frequency,
            'last_updated': last_updated_str,
            'is_editable': is_hr,
        }

        return json_response(data=salary_data)

    @http.route('/api/payroll/update', type='http', auth='public', methods=['PUT', 'OPTIONS'], csrf=False, cors='*')
    def update_salary(self, **kwargs):
        """HR endpoint to update employee salary structure."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        user, _, err = get_auth_context()
        if err:
            return err

        if not is_hr_user(user):
            return json_response(success=False, status=403, message='Access denied: HR privileges required.')

        body = get_json_body()
        employee_id = body.get('employee_id')

        if not employee_id:
            return json_response(success=False, status=400, message='employee_id is required.')

        try:
            emp_id_int = int(employee_id)
        except (ValueError, TypeError):
            return json_response(success=False, status=400, message='Invalid employee_id format.')

        payroll = request.env['dayflow.payroll'].sudo().search([('employee_id', '=', emp_id_int)], limit=1)

        vals = {'last_updated': fields.Datetime.now()}
        try:
            if 'basic_salary' in body:
                vals['basic_salary'] = float(body['basic_salary'])
            if 'hra' in body:
                vals['hra'] = float(body['hra'])
            if 'special_allowance' in body:
                vals['special_allowance'] = float(body['special_allowance'])
            if 'deductions' in body:
                vals['deductions'] = float(body['deductions'])
        except (ValueError, TypeError):
            return json_response(success=False, status=400, message='Salary fields must be valid numeric values.')

        if 'payment_frequency' in body:
            vals['payment_frequency'] = body['payment_frequency']

        if payroll:
            payroll.sudo().write(vals)
        else:
            vals['employee_id'] = emp_id_int
            payroll = request.env['dayflow.payroll'].sudo().create(vals)

        return json_response(
            data={
                'employee_id': payroll.employee_id.id,
                'gross_salary': payroll.gross_salary,
                'net_salary': payroll.net_salary,
            },
            message=f"Salary structure updated successfully for {payroll.employee_id.name}."
        )
