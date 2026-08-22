# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta
import logging
from odoo import http, fields
from odoo.http import request
from .common import json_response, options_response, get_json_body

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
                'id': None,
                'employee_id': employee.id,
                'employee_name': employee.name,
                'status': 'absent',
                'state': 'absent',
                'is_checked_in': False,
                'check_in': None,
                'check_out': None,
                'worked_hours': 0.0,
                'date': str(today),
            })

        return json_response(data={
            'id': attendance.id,
            'employee_id': employee.id,
            'employee_name': employee.name,
            'status': attendance.status,
            'state': attendance.status,
            'is_checked_in': bool(attendance.check_in and not attendance.check_out),
            'check_in': attendance.check_in.strftime('%Y-%m-%d %H:%M:%S') if attendance.check_in else None,
            'check_out': attendance.check_out.strftime('%Y-%m-%d %H:%M:%S') if attendance.check_out else None,
            'worked_hours': attendance.worked_hours,
            'date': str(attendance.date),
        })

    @http.route('/api/attendance/check-in', type='http', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def check_in(self, **kwargs):
        """
        Register check-in timestamp for the authenticated employee.
        Does not trust any client-supplied employee_id.
        """
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        employee = self._get_current_employee()
        if not employee:
            return json_response(success=False, status=404, message='Employee profile not found.')

        try:
            attendance = request.env['dayflow.attendance'].action_check_in(employee.id)
            return json_response(
                data={
                    'id': attendance.id,
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'check_in': attendance.check_in.strftime('%Y-%m-%d %H:%M:%S'),
                    'check_out': None,
                    'worked_hours': attendance.worked_hours,
                    'status': attendance.status,
                    'state': attendance.status,
                    'date': str(attendance.date),
                },
                message='Checked in successfully! Have a productive day.',
                status=201
            )
        except Exception as e:
            return json_response(
                success=False,
                status=400,
                message=str(e)
            )

    @http.route('/api/attendance/check-out', type='http', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def check_out(self, **kwargs):
        """
        Register check-out timestamp and compute worked hours for the authenticated employee.
        Does not allow an employee to check out another employee's session.
        """
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        employee = self._get_current_employee()
        if not employee:
            return json_response(success=False, status=404, message='Employee profile not found.')

        try:
            attendance = request.env['dayflow.attendance'].action_check_out(employee.id)
            return json_response(
                data={
                    'id': attendance.id,
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'check_in': attendance.check_in.strftime('%Y-%m-%d %H:%M:%S'),
                    'check_out': attendance.check_out.strftime('%Y-%m-%d %H:%M:%S'),
                    'worked_hours': attendance.worked_hours,
                    'status': attendance.status,
                    'state': attendance.status,
                    'date': str(attendance.date),
                },
                message='Checked out successfully.'
            )
        except Exception as e:
            return json_response(
                success=False,
                status=400,
                message=str(e)
            )

    @http.route(['/api/attendance/my-history', '/api/attendance/history'], type='http', auth='user', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_my_history(self, target_date=None, start_date=None, end_date=None, limit=30, **kwargs):
        """
        Retrieve historical attendance records exclusively for the authenticated employee.
        Supports daily (target_date/date) and weekly (start_date, end_date) filters.
        """
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        employee = self._get_current_employee()
        if not employee:
            return json_response(success=False, status=404, message='Employee profile not found.')

        # Accept either 'target_date' or 'date' query parameter
        query_date = target_date or kwargs.get('date')

        domain = [('employee_id', '=', employee.id)]
        if query_date:
            domain.append(('date', '=', query_date))
        if start_date:
            domain.append(('date', '>=', start_date))
        if end_date:
            domain.append(('date', '<=', end_date))

        records = request.env['dayflow.attendance'].search(
            domain,
            order='date desc, check_in desc',
            limit=int(limit) if limit else 30
        )

        data = [{
            'id': rec.id,
            'employee_id': rec.employee_id.id,
            'employee_name': rec.employee_id.name,
            'date': str(rec.date),
            'check_in': rec.check_in.strftime('%Y-%m-%d %H:%M:%S') if rec.check_in else None,
            'check_out': rec.check_out.strftime('%Y-%m-%d %H:%M:%S') if rec.check_out else None,
            'worked_hours': rec.worked_hours,
            'status': rec.status,
            'state': rec.status,
            'remarks': rec.remarks or '',
        } for rec in records]

        return json_response(data=data)

    @http.route('/api/attendance/company', type='http', auth='user', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_company_attendance(self, target_date=None, start_date=None, end_date=None, **kwargs):
        """
        HR endpoint to view company-wide daily/weekly attendance logs.
        Strictly restricted to HR / Admin users.
        """
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        user = request.env.user
        is_hr = (
            user.has_group('dayflow.group_dayflow_hr') or
            user.has_group('backend_attendance_leave.group_dayflow_hr') or
            user.id == 1
        )
        if not is_hr:
            return json_response(success=False, status=403, message='HR permissions required.')

        # Accept either 'target_date' or 'date' query parameter
        query_date = target_date or kwargs.get('date')

        domain = []
        if query_date:
            domain.append(('date', '=', query_date))
        elif not start_date and not end_date:
            domain.append(('date', '=', str(fields.Date.today())))

        if start_date:
            domain.append(('date', '>=', start_date))
        if end_date:
            domain.append(('date', '<=', end_date))

        records = request.env['dayflow.attendance'].search(
            domain,
            order='date desc, check_in desc'
        )

        data = [{
            'id': rec.id,
            'employee_id': rec.employee_id.id,
            'employee_name': rec.employee_id.name,
            'employee_code': rec.employee_id.employee_code,
            'department_name': rec.employee_id.department_name,
            'date': str(rec.date),
            'check_in': rec.check_in.strftime('%Y-%m-%d %H:%M:%S') if rec.check_in else None,
            'check_out': rec.check_out.strftime('%Y-%m-%d %H:%M:%S') if rec.check_out else None,
            'worked_hours': rec.worked_hours,
            'status': rec.status,
            'state': rec.status,
        } for rec in records]

        return json_response(data=data)
