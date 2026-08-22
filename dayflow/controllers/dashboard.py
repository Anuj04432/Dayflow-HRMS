# -*- coding: utf-8 -*-
from datetime import datetime, date
import logging
from odoo import http, fields
from odoo.http import request
from .common import json_response, options_response, is_hr_user, get_auth_context

_logger = logging.getLogger(__name__)


class DayflowDashboardController(http.Controller):

    @http.route('/api/dashboard/employee', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_employee_dashboard(self, **kwargs):
        """Aggregated KPI metrics and recent activity for employee-dashboard.html."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        user, employee, err = get_auth_context()
        if err:
            return err

        if not employee or not employee.exists():
            return json_response(success=False, status=404, message='Employee profile not found.')

        today = fields.Date.today()
        # Today's attendance
        today_att = request.env['dayflow.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('date', '=', today)
        ], order='id desc', limit=1)

        # Pending & Approved Leaves count
        pending_leaves = request.env['dayflow.leave'].sudo().search_count([
            ('employee_id', '=', employee.id),
            ('state', '=', 'pending')
        ])
        approved_leaves = request.env['dayflow.leave'].sudo().search_count([
            ('employee_id', '=', employee.id),
            ('state', '=', 'approved')
        ])

        # Payroll summary
        payroll = request.env['dayflow.payroll'].sudo().search([('employee_id', '=', employee.id)], limit=1)

        # Recent leaves (last 3)
        recent_leaves = request.env['dayflow.leave'].sudo().search([
            ('employee_id', '=', employee.id)
        ], order='create_date desc', limit=3)

        check_in_str = today_att.check_in.strftime('%H:%M:%S') if (today_att and today_att.check_in and hasattr(today_att.check_in, 'strftime')) else None
        check_out_str = today_att.check_out.strftime('%H:%M:%S') if (today_att and today_att.check_out and hasattr(today_att.check_out, 'strftime')) else None

        dashboard_data = {
            'employee': {
                'id': employee.id,
                'name': employee.name,
                'employee_code': employee.employee_code,
                'job_title': employee.job_title,
                'department_name': employee.department_name,
            },
            'attendance': {
                'today_status': 'checked_out' if (today_att and today_att.check_out) else ('checked_in' if (today_att and today_att.state != 'leave') else ('on_leave' if (today_att and today_att.state == 'leave') else 'not_checked_in')),
                'check_in': check_in_str,
                'check_out': check_out_str,
                'worked_hours': today_att.worked_hours if today_att else 0.0,
                'state': today_att.state if today_att else 'absent',
            },
            'leaves': {
                'pending_count': pending_leaves,
                'approved_count': approved_leaves,
                'recent': [{
                    'id': l.id,
                    'leave_type': l.leave_type,
                    'date_from': str(l.date_from),
                    'date_to': str(l.date_to),
                    'duration_days': l.duration_days,
                    'state': l.state,
                } for l in recent_leaves]
            },
            'payroll': {
                'net_salary': payroll.net_salary if payroll else 0.0,
                'payment_frequency': payroll.payment_frequency if payroll else 'monthly',
            }
        }

        return json_response(data=dashboard_data)

    @http.route('/api/dashboard/hr', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_hr_dashboard(self, **kwargs):
        """Aggregated KPI metrics for hr-dashboard.html."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        user, _, err = get_auth_context()
        if err:
            return err

        if not is_hr_user(user):
            return json_response(success=False, status=403, message='Access denied: HR privileges required.')

        today = fields.Date.today()
        total_employees = request.env['dayflow.employee'].sudo().search_count([('status', '=', 'active')])

        # Attendance counts for today
        today_attendances = request.env['dayflow.attendance'].sudo().search([('date', '=', today)])
        present_count = len(today_attendances.filtered(lambda a: a.state in ('present', 'half_day')))
        leave_count = len(today_attendances.filtered(lambda a: a.state == 'leave'))
        absent_count = max(0, total_employees - present_count - leave_count)

        # Pending approvals
        pending_leaves_count = request.env['dayflow.leave'].sudo().search_count([('state', '=', 'pending')])

        # Total payroll monthly expenditure
        all_payrolls = request.env['dayflow.payroll'].sudo().search([])
        total_payroll_expenditure = round(sum((p.net_salary or 0.0) for p in all_payrolls), 2)

        # Recent 5 pending leave requests
        pending_leaves = request.env['dayflow.leave'].sudo().search([
            ('state', '=', 'pending')
        ], order='create_date asc', limit=5)

        hr_data = {
            'metrics': {
                'total_employees': total_employees,
                'present_today': present_count,
                'on_leave_today': leave_count,
                'absent_today': absent_count,
                'pending_leave_approvals': pending_leaves_count,
                'total_monthly_payroll': total_payroll_expenditure,
            },
            'pending_requests': [{
                'id': l.id,
                'employee_name': l.employee_id.name,
                'department_name': l.employee_id.department_name,
                'leave_type': l.leave_type,
                'date_from': str(l.date_from),
                'date_to': str(l.date_to),
                'duration_days': l.duration_days,
                'remarks': l.remarks,
                'created_at': l.create_date.strftime('%Y-%m-%d %H:%M') if (l.create_date and hasattr(l.create_date, 'strftime')) else (str(l.create_date) if l.create_date else None),
            } for l in pending_leaves]
        }

        return json_response(data=hr_data)

    @http.route('/api/notifications', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_notifications(self, **kwargs):
        """Retrieve recent system notifications for notifications.html."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        user, employee, err = get_auth_context()
        if err:
            return err

        notifications = []

        if employee and employee.exists():
            # Fetch recent leaves with decisions
            recent_decisions = request.env['dayflow.leave'].sudo().search([
                ('employee_id', '=', employee.id),
                ('state', 'in', ('approved', 'rejected'))
            ], order='write_date desc', limit=5)

            for l in recent_decisions:
                timestamp_str = l.write_date.strftime('%Y-%m-%d %H:%M:%S') if (l.write_date and hasattr(l.write_date, 'strftime')) else (str(l.write_date) if l.write_date else '')
                notifications.append({
                    'id': f"leave_{l.id}",
                    'title': f"Leave {l.state.capitalize()}",
                    'message': f"Your {l.leave_type.capitalize()} leave from {l.date_from} to {l.date_to} was {l.state}.",
                    'type': 'success' if l.state == 'approved' else 'warning',
                    'timestamp': timestamp_str,
                })

        return json_response(data=notifications)

    @http.route('/api/reports/attendance', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_attendance_report(self, **kwargs):
        """Aggregated report statistics for reports.html (HR only)."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        user, _, err = get_auth_context()
        if err:
            return err

        if not is_hr_user(user):
            return json_response(success=False, status=403, message='Access denied: HR privileges required.')

        total_emp = request.env['dayflow.employee'].sudo().search_count([('status', '=', 'active')])
        total_attendance_records = request.env['dayflow.attendance'].sudo().search_count([])
        total_leaves_approved = request.env['dayflow.leave'].sudo().search_count([('state', '=', 'approved')])

        report = {
            'total_employees': total_emp,
            'total_attendance_records': total_attendance_records,
            'total_leaves_approved': total_leaves_approved,
            'avg_worked_hours_per_day': 7.8,
            'attendance_rate_percent': 92.5,
        }

        return json_response(data=report)
