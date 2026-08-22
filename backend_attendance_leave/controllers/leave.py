# -*- coding: utf-8 -*-
from datetime import datetime, date
import logging
from odoo import http, fields
from odoo.http import request
from .common import json_response, options_response, get_json_body

_logger = logging.getLogger(__name__)


class DayflowLeaveController(http.Controller):

    def _get_current_employee(self):
        user = request.env.user
        return user.dayflow_employee_id or request.env['dayflow.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

    @http.route('/api/leave/types', type='http', auth='user', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_leave_types(self, **kwargs):
        """Retrieve available leave types for Dayflow HRMS."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        types = [
            {'id': 'paid', 'name': 'Paid Time Off (PTO)'},
            {'id': 'sick', 'name': 'Sick Leave'},
            {'id': 'unpaid', 'name': 'Unpaid Leave'},
        ]
        return json_response(data=types)

    @http.route('/api/leave/apply', type='http', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def apply_leave(self, **kwargs):
        """
        Submit a new leave application for the authenticated employee.
        Does not trust any client-supplied employee_id.
        """
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        employee = self._get_current_employee()
        if not employee:
            return json_response(success=False, status=404, message='Employee profile not found.')

        body = get_json_body()
        leave_type = body.get('leave_type')
        date_from = body.get('date_from') or body.get('request_date_from')
        date_to = body.get('date_to') or body.get('request_date_to')
        remarks = (body.get('remarks') or body.get('name') or '').strip()

        if not leave_type or not date_from or not date_to or not remarks:
            return json_response(
                success=False,
                status=400,
                message='All fields are required: leave_type, date_from, date_to, and remarks.'
            )

        if leave_type not in ('paid', 'sick', 'unpaid'):
            return json_response(
                success=False,
                status=400,
                message='Invalid leave_type. Must be paid, sick, or unpaid.'
            )

        try:
            d_from = datetime.strptime(date_from, '%Y-%m-%d').date() if isinstance(date_from, str) else date_from
            d_to = datetime.strptime(date_to, '%Y-%m-%d').date() if isinstance(date_to, str) else date_to
            if d_to < d_from:
                return json_response(success=False, status=400, message='End date cannot be before start date.')
        except ValueError:
            return json_response(success=False, status=400, message='Invalid date format. Use YYYY-MM-DD.')

        try:
            leave_req = request.env['dayflow.leave'].action_apply_leave(
                employee_id=employee.id,
                leave_type=leave_type,
                date_from=d_from,
                date_to=d_to,
                remarks=remarks,
            )
            return json_response(
                data={
                    'id': leave_req.id,
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'leave_type': leave_req.leave_type,
                    'request_date_from': str(leave_req.date_from),
                    'request_date_to': str(leave_req.date_to),
                    'date_from': str(leave_req.date_from),
                    'date_to': str(leave_req.date_to),
                    'number_of_days': leave_req.duration_days,
                    'duration_days': leave_req.duration_days,
                    'name': leave_req.remarks,
                    'remarks': leave_req.remarks,
                    'state': leave_req.state,
                    'hr_comments': leave_req.hr_comments or '',
                },
                message='Leave request submitted successfully. Awaiting HR approval.',
                status=201
            )
        except Exception as e:
            return json_response(
                success=False,
                status=400,
                message=str(e)
            )

    @http.route('/api/leave/my-requests', type='http', auth='user', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_my_leaves(self, **kwargs):
        """Retrieve leave requests submitted exclusively by the authenticated employee."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        employee = self._get_current_employee()
        if not employee:
            return json_response(success=False, status=404, message='Employee profile not found.')

        requests = request.env['dayflow.leave'].search(
            [('employee_id', '=', employee.id)],
            order='create_date desc'
        )

        data = [{
            'id': req.id,
            'employee_id': req.employee_id.id,
            'employee_name': req.employee_id.name,
            'leave_type': req.leave_type,
            'request_date_from': str(req.date_from),
            'request_date_to': str(req.date_to),
            'date_from': str(req.date_from),
            'date_to': str(req.date_to),
            'number_of_days': req.duration_days,
            'duration_days': req.duration_days,
            'name': req.remarks,
            'remarks': req.remarks,
            'state': req.state,
            'hr_comments': req.hr_comments or req.manager_remarks or '',
            'manager_remarks': req.manager_remarks or '',
            'created_at': req.create_date.strftime('%Y-%m-%d %H:%M:%S') if req.create_date else None,
        } for req in requests]

        return json_response(data=data)

    @http.route(['/api/leave/pending-approvals', '/api/leave/pending'], type='http', auth='user', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_pending_leaves(self, **kwargs):
        """
        HR endpoint to fetch all pending leave requests requiring approval.
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
            return json_response(success=False, status=403, message='Access denied: HR privileges required.')

        pending_requests = request.env['dayflow.leave'].search(
            [('state', '=', 'pending')],
            order='create_date asc'
        )

        data = [{
            'id': req.id,
            'employee_id': req.employee_id.id,
            'employee_name': req.employee_id.name,
            'employee_code': req.employee_id.employee_code,
            'department_name': req.employee_id.department_name,
            'leave_type': req.leave_type,
            'request_date_from': str(req.date_from),
            'request_date_to': str(req.date_to),
            'date_from': str(req.date_from),
            'date_to': str(req.date_to),
            'number_of_days': req.duration_days,
            'duration_days': req.duration_days,
            'name': req.remarks,
            'remarks': req.remarks,
            'state': req.state,
            'approved_by': req.approved_by.id if req.approved_by else None,
            'hr_comments': req.hr_comments or req.manager_remarks or '',
            'created_at': req.create_date.strftime('%Y-%m-%d %H:%M:%S') if req.create_date else None,
        } for req in pending_requests]

        return json_response(data=data)

    @http.route('/api/leave/approve', type='http', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def approve_leave(self, **kwargs):
        """
        HR action handler to approve a pending leave request.
        Strictly verifies HR permission, ensures pending state, and tracks reviewer.
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
            return json_response(success=False, status=403, message='Access denied: HR privileges required.')

        body = get_json_body()
        leave_id = body.get('leave_id')
        comments = (body.get('hr_comments') or body.get('comments') or '').strip()

        if not leave_id:
            return json_response(success=False, status=400, message="Missing required parameter: 'leave_id'.")

        try:
            leave_id_int = int(leave_id)
        except (ValueError, TypeError):
            return json_response(success=False, status=400, message="Invalid 'leave_id' format. Must be an integer.")

        leave_req = request.env['dayflow.leave'].browse(leave_id_int)
        if not leave_req.exists():
            return json_response(success=False, status=404, message='Leave request not found.')

        if leave_req.state != 'pending':
            return json_response(
                success=False,
                status=400,
                message=f"Cannot approve leave request in '{leave_req.state}' state. Only pending requests can be approved."
            )

        try:
            leave_req.action_approve(comments=comments)
            return json_response(
                data={
                    'id': leave_req.id,
                    'employee_id': leave_req.employee_id.id,
                    'employee_name': leave_req.employee_id.name,
                    'leave_type': leave_req.leave_type,
                    'request_date_from': str(leave_req.date_from),
                    'request_date_to': str(leave_req.date_to),
                    'date_from': str(leave_req.date_from),
                    'date_to': str(leave_req.date_to),
                    'number_of_days': leave_req.duration_days,
                    'duration_days': leave_req.duration_days,
                    'name': leave_req.remarks,
                    'remarks': leave_req.remarks,
                    'state': leave_req.state,
                    'approved_by': leave_req.approved_by.id if leave_req.approved_by else user.id,
                    'hr_comments': leave_req.hr_comments or '',
                },
                message=f"Leave request for {leave_req.employee_id.name} has been APPROVED."
            )
        except Exception as e:
            return json_response(success=False, status=400, message=str(e))

    @http.route('/api/leave/reject', type='http', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def reject_leave(self, **kwargs):
        """
        HR action handler to reject a pending leave request.
        Requires HR comments explaining the rejection reason.
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
            return json_response(success=False, status=403, message='Access denied: HR privileges required.')

        body = get_json_body()
        leave_id = body.get('leave_id')
        comments = (body.get('hr_comments') or body.get('comments') or '').strip()

        if not leave_id:
            return json_response(success=False, status=400, message="Missing required parameter: 'leave_id'.")

        if not comments:
            return json_response(
                success=False,
                status=400,
                message="HR comments explaining the reason for rejection are required."
            )

        try:
            leave_id_int = int(leave_id)
        except (ValueError, TypeError):
            return json_response(success=False, status=400, message="Invalid 'leave_id' format. Must be an integer.")

        leave_req = request.env['dayflow.leave'].browse(leave_id_int)
        if not leave_req.exists():
            return json_response(success=False, status=404, message='Leave request not found.')

        if leave_req.state != 'pending':
            return json_response(
                success=False,
                status=400,
                message=f"Cannot reject leave request in '{leave_req.state}' state. Only pending requests can be rejected."
            )

        try:
            leave_req.action_reject(comments=comments)
            return json_response(
                data={
                    'id': leave_req.id,
                    'employee_id': leave_req.employee_id.id,
                    'employee_name': leave_req.employee_id.name,
                    'leave_type': leave_req.leave_type,
                    'request_date_from': str(leave_req.date_from),
                    'request_date_to': str(leave_req.date_to),
                    'date_from': str(leave_req.date_from),
                    'date_to': str(leave_req.date_to),
                    'number_of_days': leave_req.duration_days,
                    'duration_days': leave_req.duration_days,
                    'name': leave_req.remarks,
                    'remarks': leave_req.remarks,
                    'state': leave_req.state,
                    'approved_by': leave_req.approved_by.id if leave_req.approved_by else user.id,
                    'hr_comments': leave_req.hr_comments or '',
                },
                message=f"Leave request for {leave_req.employee_id.name} has been REJECTED."
            )
        except Exception as e:
            return json_response(success=False, status=400, message=str(e))

    @http.route('/api/leave/action', type='http', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def process_leave_action(self, **kwargs):
        """Backward-compatible action router for approve / reject."""
        body = get_json_body()
        action = body.get('action')
        if action == 'approve':
            return self.approve_leave(**kwargs)
        elif action == 'reject':
            return self.reject_leave(**kwargs)
        return json_response(
            success=False,
            status=400,
            message="Invalid request. Provide 'action' ('approve' or 'reject')."
        )
