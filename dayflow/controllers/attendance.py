# -*- coding: utf-8 -*-
from datetime import datetime, date
import logging
from odoo import http, fields
from odoo.http import request
from .common import json_response, options_response, get_json_body, is_hr_user, get_auth_context

_logger = logging.getLogger(__name__)


class DayflowAttendanceController(http.Controller):

    @http.route('/api/attendance/today', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_today_attendance(self, **kwargs):
        """Retrieve today's attendance status for logged-in employee."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        user, employee, err = get_auth_context()
        if err:
            return err

        if not employee or not employee.exists():
            return json_response(success=False, status=404, message='Employee profile not found.')

        today = fields.Date.today()
        attendance = request.env['dayflow.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('date', '=', today)
        ], order='id desc', limit=1)

        if not attendance:
            # Check if employee has approved leave today
            approved_leave = request.env['dayflow.leave'].sudo().search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'approved'),
                ('date_from', '<=', today),
                ('date_to', '>=', today),
            ], limit=1)

            if approved_leave:
                return json_response(data={
                    'status': 'on_leave',
                    'state': 'leave',
                    'leave_type': approved_leave.leave_type,
                    'check_in': None,
                    'check_out': None,
                    'worked_hours': 0.0,
                    'date': str(today),
                })

            return json_response(data={
                'status': 'not_checked_in',
                'state': 'not_checked_in',
                'leave_type': None,
                'check_in': None,
                'check_out': None,
                'worked_hours': 0.0,
                'date': str(today),
            })

        check_in_str = attendance.check_in.strftime('%Y-%m-%d %H:%M:%S') if (attendance.check_in and hasattr(attendance.check_in, 'strftime')) else (str(attendance.check_in) if attendance.check_in else None)
        check_out_str = attendance.check_out.strftime('%Y-%m-%d %H:%M:%S') if (attendance.check_out and hasattr(attendance.check_out, 'strftime')) else (str(attendance.check_out) if attendance.check_out else None)

        return json_response(data={
            'id': attendance.id,
            'status': 'checked_out' if attendance.check_out else 'checked_in',
            'state': attendance.state,
            'check_in': check_in_str,
            'check_out': check_out_str,
            'worked_hours': attendance.worked_hours,
            'date': str(attendance.date),
        })

    @http.route('/api/attendance/check-in', type='http', auth='public', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def check_in(self, **kwargs):
        """Register check-in timestamp."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        user, employee, err = get_auth_context()
        if err:
            return err

        if not employee or not employee.exists():
            return json_response(success=False, status=404, message='Employee profile not found.')

        today = fields.Date.today()
        # Check if already active
        existing_active = request.env['dayflow.attendance'].sudo().search([
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
        attendance = request.env['dayflow.attendance'].sudo().create({
            'employee_id': employee.id,
            'date': today,
            'check_in': now,
            'state': 'present',
        })

        check_in_str = attendance.check_in.strftime('%Y-%m-%d %H:%M:%S') if (attendance.check_in and hasattr(attendance.check_in, 'strftime')) else str(attendance.check_in)

        return json_response(
            data={
                'id': attendance.id,
                'check_in': check_in_str,
                'state': attendance.state,
            },
            message='Checked in successfully! Have a productive day.',
            status=201
        )

    @http.route('/api/attendance/check-out', type='http', auth='public', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def check_out(self, **kwargs):
        """Register check-out timestamp and compute worked hours."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        user, employee, err = get_auth_context()
        if err:
            return err

        if not employee or not employee.exists():
            return json_response(success=False, status=404, message='Employee profile not found.')

        today = fields.Date.today()
        active_attendance = request.env['dayflow.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('date', '=', today),
            ('check_out', '=', False)
        ], order='id desc', limit=1)

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

        check_in_str = active_attendance.check_in.strftime('%Y-%m-%d %H:%M:%S') if (active_attendance.check_in and hasattr(active_attendance.check_in, 'strftime')) else str(active_attendance.check_in)
        check_out_str = active_attendance.check_out.strftime('%Y-%m-%d %H:%M:%S') if (active_attendance.check_out and hasattr(active_attendance.check_out, 'strftime')) else str(active_attendance.check_out)

        return json_response(
            data={
                'id': active_attendance.id,
                'check_in': check_in_str,
                'check_out': check_out_str,
                'worked_hours': active_attendance.worked_hours,
                'state': active_attendance.state,
            },
            message='Checked out successfully.'
        )

    @http.route('/api/attendance/history', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_history(self, limit=30, **kwargs):
        """Retrieve historical attendance records for current employee."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        user, employee, err = get_auth_context()
        if err:
            return err

        if not employee or not employee.exists():
            return json_response(success=False, status=404, message='Employee profile not found.')

        try:
            limit_val = int(limit)
        except (ValueError, TypeError):
            limit_val = 30

        records = request.env['dayflow.attendance'].sudo().search(
            [('employee_id', '=', employee.id)],
            order='date desc, check_in desc',
            limit=limit_val
        )

        data = [{
            'id': rec.id,
            'date': str(rec.date),
            'check_in': rec.check_in.strftime('%Y-%m-%d %H:%M:%S') if (rec.check_in and hasattr(rec.check_in, 'strftime')) else (str(rec.check_in) if rec.check_in else None),
            'check_out': rec.check_out.strftime('%Y-%m-%d %H:%M:%S') if (rec.check_out and hasattr(rec.check_out, 'strftime')) else (str(rec.check_out) if rec.check_out else None),
            'worked_hours': rec.worked_hours,
            'state': rec.state,
            'remarks': rec.remarks or '',
        } for rec in records]

        return json_response(data=data)

    @http.route('/api/attendance/company', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_company_attendance(self, target_date=None, **kwargs):
        """HR endpoint to view company-wide daily attendance logs."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        user, _, err = get_auth_context()
        if err:
            return err

        if not is_hr_user(user):
            return json_response(success=False, status=403, message='HR permissions required.')

        query_date = target_date or str(fields.Date.today())
        records = request.env['dayflow.attendance'].sudo().search(
            [('date', '=', query_date)],
            order='check_in desc'
        )

        data = [{
            'id': rec.id,
            'employee_name': rec.employee_id.name,
            'employee_code': rec.employee_id.employee_code,
            'department_name': rec.employee_id.department_name,
            'date': str(rec.date),
            'check_in': rec.check_in.strftime('%H:%M:%S') if (rec.check_in and hasattr(rec.check_in, 'strftime')) else (str(rec.check_in) if rec.check_in else None),
            'check_out': rec.check_out.strftime('%H:%M:%S') if (rec.check_out and hasattr(rec.check_out, 'strftime')) else (str(rec.check_out) if rec.check_out else None),
            'worked_hours': rec.worked_hours,
            'state': rec.state,
        } for rec in records]

        return json_response(data=data)
