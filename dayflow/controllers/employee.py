# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request
from .common import json_response, options_response, get_json_body, is_hr_user, get_auth_context

_logger = logging.getLogger(__name__)


class DayflowEmployeeController(http.Controller):

    @http.route('/api/employee/profile', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_profile(self, employee_id=None, **kwargs):
        """Retrieve employee profile. Employees get their own; HR can pass employee_id."""
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
            return json_response(success=False, status=404, message='Employee profile not found.')

        photo_str = None
        if employee.image_1920:
            if isinstance(employee.image_1920, bytes):
                photo_str = employee.image_1920.decode('utf-8')
            else:
                photo_str = str(employee.image_1920)

        profile_data = {
            'id': employee.id,
            'name': employee.name,
            'employee_code': employee.employee_code,
            'work_email': employee.work_email,
            'phone': employee.phone or '',
            'address': employee.address or '',
            'job_title': employee.job_title or '',
            'department_name': employee.department_name or '',
            'join_date': str(employee.join_date) if employee.join_date else '',
            'status': employee.status,
            'has_photo': bool(employee.image_1920),
            'image_1920': photo_str,
        }

        return json_response(data=profile_data)

    @http.route('/api/employee/profile', type='http', auth='public', methods=['PUT', 'OPTIONS'], csrf=False, cors='*')
    def update_profile(self, **kwargs):
        """Update employee profile. Restricts fields according to Dayflow RBAC rules."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        user, current_employee, err = get_auth_context()
        if err:
            return err

        body = get_json_body()
        is_hr = is_hr_user(user)

        target_emp_id = body.get('employee_id')
        if target_emp_id and is_hr:
            try:
                target_id_int = int(target_emp_id)
                employee = request.env['dayflow.employee'].sudo().browse(target_id_int)
            except (ValueError, TypeError):
                return json_response(success=False, status=400, message='Invalid employee_id.')
        else:
            employee = current_employee

        if not employee or not employee.exists():
            return json_response(success=False, status=404, message='Employee profile not found.')

        vals = {}
        # Fields editable by employee
        if 'phone' in body:
            vals['phone'] = (body['phone'] or '').strip()
        if 'address' in body:
            vals['address'] = (body['address'] or '').strip()
        if 'image_1920' in body:
            vals['image_1920'] = body['image_1920']

        # Fields editable ONLY by HR
        if is_hr:
            if 'name' in body and body['name']:
                vals['name'] = str(body['name']).strip()
            if 'job_title' in body and body['job_title']:
                vals['job_title'] = str(body['job_title']).strip()
            if 'department_name' in body and body['department_name']:
                vals['department_name'] = str(body['department_name']).strip()
            if 'status' in body and body['status']:
                vals['status'] = body['status']

        try:
            employee.update_permitted_profile(vals)
            return json_response(message='Profile updated successfully.')
        except Exception as e:
            _logger.exception("Profile update error: %s", str(e))
            return json_response(success=False, status=400, message=str(e))

    @http.route('/api/employee/list', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_employee_list(self, **kwargs):
        """HR endpoint to retrieve list of all company employees."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        user, _, err = get_auth_context()
        if err:
            return err

        if not is_hr_user(user):
            return json_response(success=False, status=403, message='Access denied: HR privileges required.')

        employees = request.env['dayflow.employee'].sudo().search([])
        emp_list = [{
            'id': emp.id,
            'name': emp.name,
            'employee_code': emp.employee_code,
            'work_email': emp.work_email,
            'phone': emp.phone or '',
            'job_title': emp.job_title or '',
            'department_name': emp.department_name or '',
            'status': emp.status,
            'join_date': str(emp.join_date) if emp.join_date else '',
        } for emp in employees]

        return json_response(data=emp_list)
