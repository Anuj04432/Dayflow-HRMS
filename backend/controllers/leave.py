# -*- coding: utf-8 -*-
from datetime import datetime, date
import logging
from odoo import http, fields
from odoo.http import request
from .common import json_response, options_response, get_json_body, is_hr_user

_logger = logging.getLogger(__name__)


class DayflowLeaveController(http.Controller):

    def _get_current_employee(self):
        user = request.env.user
        return user.dayflow_employee_id or request.env['dayflow.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

    @http.route('/api/leave/types', type='http', auth='user', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_leave_types(self, **kwargs):
        """Retrieve available leave types."""
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
        """Submit a new leave application."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        employee = self._get_current_employee()
        if not employee:
            return json_response(success=False, status=404, message='Employee profile not found.')

        body = get_json_body()
        leave_type = body.get('leave_type')
        date_from = body.get('date_from')
        date_to = body.get('date_to')
        remarks = (body.get('remarks') or '').strip()

        if not leave_type or not date_from or not date_to or not remarks:
            return json_response(
                success=False,
                status=400,
                message='All fields are required: leave_type, date_from, date_to, and remarks.'
            )

        try:
            d_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            d_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            if d_to < d_from:
                return json_response(success=False, status=400, message='End date cannot be before start date.')
        except ValueError:
            return json_response(success=False, status=400, message='Invalid date format. Use YYYY-MM-DD.')

        leave_req = request.env['dayflow.leave'].create({
            'employee_id': employee.id,
            'leave_type': leave_type,
            'date_from': d_from,
            'date_to': d_to,
            'remarks': remarks,
            'state': 'pending',
        })

        return json_response(
            data={
                'id': leave_req.id,
                'leave_type': leave_req.leave_type,
                'date_from': str(leave_req.date_from),
                'date_to': str(leave_req.date_to),
                'duration_days': leave_req.duration_days,
                'state': leave_req.state,
            },
            message='Leave request submitted successfully. Awaiting HR approval.',
            status=201
        )

    @http.route('/api/leave/my-requests', type='http', auth='user', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_my_leaves(self, **kwargs):
        """Retrieve leave requests submitted by the logged-in employee."""
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
            'leave_type': req.leave_type,
            'date_from': str(req.date_from),
            'date_to': str(req.date_to),
            'duration_days': req.duration_days,
            'remarks': req.remarks,
            'state': req.state,
            'manager_remarks': req.manager_remarks or '',
            'created_at': req.create_date.strftime('%Y-%m-%d %H:%M:%S') if req.create_date else None,
        } for req in requests]

        return json_response(data=data)

    @http.route('/api/leave/pending', type='http', auth='user', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_pending_leaves(self, **kwargs):
        """HR endpoint to fetch all pending leave requests requiring approval."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        if not is_hr_user(request.env.user):
            return json_response(success=False, status=403, message='Access denied: HR privileges required.')

        pending_requests = request.env['dayflow.leave'].search(
            [('state', '=', 'pending')],
            order='create_date asc'
        )

        data = [{
            'id': req.id,
            'employee_name': req.employee_id.name,
            'employee_code': req.employee_id.employee_code,
            'department_name': req.employee_id.department_name,
            'leave_type': req.leave_type,
            'date_from': str(req.date_from),
            'date_to': str(req.date_to),
            'duration_days': req.duration_days,
            'remarks': req.remarks,
            'created_at': req.create_date.strftime('%Y-%m-%d %H:%M:%S') if req.create_date else None,
        } for req in pending_requests]

        return json_response(data=data)

    @http.route('/api/leave/all-history', type='http', auth='user', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_all_leave_history(self, **kwargs):
        """HR endpoint to fetch all historical leave logs company-wide."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        if not is_hr_user(request.env.user):
            return json_response(success=False, status=403, message='Access denied: HR privileges required.')

        all_leaves = request.env['dayflow.leave'].search([], order='create_date desc')

        data = [{
            'id': req.id,
            'employee_id': req.employee_id.id,
            'employee_name': req.employee_id.name,
            'employee_code': req.employee_id.employee_code,
            'department_name': req.employee_id.department_name,
            'leave_type': req.leave_type,
            'date_from': str(req.date_from),
            'date_to': str(req.date_to),
            'duration_days': req.duration_days,
            'remarks': req.remarks,
            'state': req.state,
            'manager_remarks': req.manager_remarks or '',
            'created_at': req.create_date.strftime('%Y-%m-%d %H:%M:%S') if req.create_date else None,
        } for req in all_leaves]

        return json_response(data=data)

    @http.route('/api/leave/action', type='http', auth='user', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def process_leave_action(self, **kwargs):
        """HR action handler to approve or reject a leave request."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        if not is_hr_user(request.env.user):
            return json_response(success=False, status=403, message='Access denied: HR privileges required.')

        body = get_json_body()
        leave_id = body.get('leave_id')
        action = body.get('action')  # 'approve' or 'reject'
        comments = (body.get('comments') or '').strip()

        if not leave_id or action not in ('approve', 'reject'):
            return json_response(
                success=False,
                status=400,
                message="Invalid request. Provide 'leave_id' and 'action' ('approve' or 'reject')."
            )

        if action == 'reject' and not comments:
            return json_response(
                success=False,
                status=400,
                message="HR comments are required when rejecting a leave request."
            )

        leave_req = request.env['dayflow.leave'].browse(int(leave_id))
        if not leave_req.exists():
            return json_response(success=False, status=404, message='Leave request not found.')

        if action == 'approve':
            leave_req.action_approve(comments=comments)
            msg = f"Leave request for {leave_req.employee_id.name} has been APPROVED."
        else:
            leave_req.action_reject(comments=comments)
            msg = f"Leave request for {leave_req.employee_id.name} has been REJECTED."

        return json_response(
            data={
                'id': leave_req.id,
                'state': leave_req.state,
                'manager_remarks': leave_req.manager_remarks,
            },
            message=msg
        )
