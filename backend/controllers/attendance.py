# -*- coding: utf-8 -*-
from datetime import datetime, date
import logging
from odoo import http, fields
from odoo.http import request
from .common import json_response, options_response, get_json_body, is_hr_user

_logger = logging.getLogger(__name__)


class DayflowAttendanceController(http.Controller):

    def _get_current_employee(self):
        user = request.env.user
        return user.dayflow_employee_id or request.env['dayflow.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

    @http.route('/api/attendance/today', type='http', auth='user', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_today_attendance(self, **kwargs):
        """Retrieve today's attendance status for logged-in employee."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        employee = self._get_current_employee()
        if not employee:
            return json_response(success=False, status=404, message='Employee profile not found.')

        today = fields.Date.today()
        attendance = request.env['dayflow.attendance'].search([
            ('employee_id', '=', employee.id),
            ('date', '=', today)
        ], order='id desc', limit=1)

        if not attendance:
            return json_response(data={
                'status': 'not_checked_in',
                'check_in': None,
                'check_out': None,
                'worked_hours': 0.0,
                'date': str(today),
            })

        return json_response(data={
            'id': attendance.id,
            'status': 'checked_out' if attendance.check_out else 'checked_in',
            'state': attendance.state,
            'check_in': attendance.check_in.strftime('%Y-%m-%d %H:%M:%S') if attendance.check_in else None,
            'check_out': attendance.check_out.strftime('%Y-%m-%d %H:%M:%S') if attendance.check_out else None,
            'worked_hours': attendance.worked_hours,
            'date': str(attendance.date),
        })

    @http.route('/api/attendance/check-in', type='http', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def check_in(self, **kwargs):
        """Register check-in timestamp."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        employee = self._get_current_employee()
        if not employee:
            return json_response(success=False, status=404, message='Employee profile not found.')

        today = fields.Date.today()
        # Check if already active
        existing_active = request.env['dayflow.attendance'].search([
            ('employee_id', '=', employee.id),
            ('date', '=', today),
            ('check_out', '=', False)
        ], limit=1)

        if existing_active:
            return json_response(
                success=False,
                status=400,
                message='You are already checked in. Please check out first before checking in again.'
            )

        now = fields.Datetime.now()
        attendance = request.env['dayflow.attendance'].create({
            'employee_id': employee.id,
            'date': today,
            'check_in': now,
            'state': 'present',
        })

        return json_response(
            data={
                'id': attendance.id,
                'check_in': attendance.check_in.strftime('%Y-%m-%d %H:%M:%S'),
                'state': attendance.state,
            },
            message='Checked in successfully! Have a productive day.',
            status=201
        )

    @http.route('/api/attendance/check-out', type='http', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def check_out(self, **kwargs):
        """Register check-out timestamp and compute worked hours."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        employee = self._get_current_employee()
        if not employee:
            return json_response(success=False, status=404, message='Employee profile not found.')

        active_attendance = request.env['dayflow.attendance'].search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False)
        ], order='check_in desc', limit=1)

        if not active_attendance:
            return json_response(
                success=False,
                status=400,
                message='No active check-in found for today. Please check in first.'
            )

        now = fields.Datetime.now()
        active_attendance.write({'check_out': now})
        
        # Classify half day if worked hours < 4
        if active_attendance.worked_hours < 4.0:
            active_attendance.write({'state': 'half_day'})

        return json_response(
            data={
                'id': active_attendance.id,
                'check_in': active_attendance.check_in.strftime('%Y-%m-%d %H:%M:%S'),
                'check_out': active_attendance.check_out.strftime('%Y-%m-%d %H:%M:%S'),
                'worked_hours': active_attendance.worked_hours,
                'state': active_attendance.state,
            },
            message='Checked out successfully.'
        )

    @http.route('/api/attendance/history', type='http', auth='user', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_history(self, limit=30, **kwargs):
        """Retrieve historical attendance records for current employee."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        employee = self._get_current_employee()
        if not employee:
            return json_response(success=False, status=404, message='Employee profile not found.')

        records = request.env['dayflow.attendance'].search(
            [('employee_id', '=', employee.id)],
            order='date desc, check_in desc',
            limit=int(limit)
        )

        data = [{
            'id': rec.id,
            'date': str(rec.date),
            'check_in': rec.check_in.strftime('%Y-%m-%d %H:%M:%S') if rec.check_in else None,
            'check_out': rec.check_out.strftime('%Y-%m-%d %H:%M:%S') if rec.check_out else None,
            'worked_hours': rec.worked_hours,
            'state': rec.state,
            'remarks': rec.remarks or '',
        } for rec in records]

        return json_response(data=data)

    @http.route('/api/attendance/company', type='http', auth='user', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_company_attendance(self, target_date=None, department=None, **kwargs):
        """HR endpoint to view company-wide attendance logs with date & department filters."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        if not is_hr_user(request.env.user):
            return json_response(success=False, status=403, message='Access denied: HR privileges required.')

        query_date = target_date or kwargs.get('date') or str(fields.Date.today())
        emp_domain = [('status', '=', 'active')]
        if department or kwargs.get('department'):
            emp_domain.append(('department_name', 'ilike', department or kwargs.get('department')))

        employees = request.env['dayflow.employee'].search(emp_domain)
        attendances = request.env['dayflow.attendance'].search([
            ('date', '=', query_date),
            ('employee_id', 'in', employees.ids)
        ])

        att_by_emp = {att.employee_id.id: att for att in attendances}

        data = []
        for emp in employees:
            att = att_by_emp.get(emp.id)
            if att:
                data.append({
                    'id': att.id,
                    'employee_id': emp.id,
                    'employee_name': emp.name,
                    'employee_code': emp.employee_code,
                    'department_name': emp.department_name,
                    'date': str(att.date),
                    'check_in': att.check_in.strftime('%H:%M:%S') if att.check_in else None,
                    'check_out': att.check_out.strftime('%H:%M:%S') if att.check_out else None,
                    'worked_hours': att.worked_hours,
                    'state': att.state,
                    'remarks': att.remarks or '',
                })
            else:
                data.append({
                    'id': None,
                    'employee_id': emp.id,
                    'employee_name': emp.name,
                    'employee_code': emp.employee_code,
                    'department_name': emp.department_name,
                    'date': query_date,
                    'check_in': None,
                    'check_out': None,
                    'worked_hours': 0.0,
                    'state': 'absent',
                    'remarks': 'Not checked in',
                })

        return json_response(data=data)
