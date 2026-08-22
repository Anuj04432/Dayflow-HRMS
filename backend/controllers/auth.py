# -*- coding: utf-8 -*-
import uuid
import logging
from odoo import http
from odoo.http import request
from .common import json_response, options_response, get_json_body, is_hr_user

_logger = logging.getLogger(__name__)


class DayflowAuthController(http.Controller):

    @http.route('/api/auth/login', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def login(self, **kwargs):
        """Authenticate user and return role/session details for frontend redirection."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        body = get_json_body()
        email = (body.get('email') or '').strip()
        password = body.get('password') or ''

        if not email or not password:
            return json_response(success=False, status=400, message='Email and password are required.')

        db = request.session.db or http.db_monodb()
        if not db:
            # Fallback to current database if available
            db = request.env.cr.dbname if hasattr(request, 'env') and request.env.cr else False
        if not db and hasattr(http, 'db_list'):
            try:
                available_dbs = http.db_list()
                if available_dbs:
                    db = available_dbs[0]
            except Exception:
                pass

        try:
            # Authenticate via Odoo session
            uid = request.session.authenticate(db, email, password)
            if not uid:
                return json_response(success=False, status=401, message='Invalid email or password.')

            user = request.env['res.users'].sudo().browse(uid)
            
            # Check verification (Admin is exempted)
            if not user.is_verified and user.id != 1 and user.login != 'admin':
                return json_response(
                    success=False,
                    status=403,
                    message='Email is not verified. Please verify your email before logging in.'
                )

            # Get linked employee profile
            employee = user.dayflow_employee_id or request.env['dayflow.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            
            # Determine effective role
            role = 'hr' if is_hr_user(user) else 'employee'

            user_data = {
                'user_id': user.id,
                'employee_id': employee.id if employee else None,
                'name': employee.name if employee else user.name,
                'email': user.login,
                'role': role,
                'employee_code': employee.employee_code if employee else None,
                'session_id': request.session.sid,
            }

            return json_response(data=user_data, message='Login successful.')

        except Exception as e:
            _logger.exception("Login error for user %s: %s", email, str(e))
            return json_response(success=False, status=401, message='Authentication failed: Invalid credentials.')

    @http.route('/api/auth/signup', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def signup(self, **kwargs):
        """Register a new user and linked employee profile, with verification token."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        body = get_json_body()
        name = (body.get('name') or '').strip()
        email = (body.get('email') or '').strip().lower()
        password = body.get('password') or ''
        role = body.get('role', 'employee')
        employee_code = (body.get('employee_code') or '').strip()
        phone = (body.get('phone') or '').strip()
        job_title = body.get('job_title', 'Software Engineer')
        department = body.get('department_name', 'Engineering')

        if not name or not email or not password:
            return json_response(success=False, status=400, message='Name, email, and password are required.')

        env = request.env(user=1)

        # Check for existing user or employee with this email
        existing_user = env['res.users'].sudo().search([('login', '=', email)], limit=1)
        if existing_user:
            return json_response(success=False, status=409, message='An account with this email already exists.')

        try:
            # Generate unique employee code if not supplied
            if not employee_code:
                last_emp = env['dayflow.employee'].sudo().search([], order='id desc', limit=1)
                next_id = (last_emp.id + 1) if last_emp else 1
                employee_code = f"DF{next_id:04d}"

            verification_token = str(uuid.uuid4())

            # Create User
            user_vals = {
                'name': name,
                'login': email,
                'password': password,
                'email': email,
                'is_verified': False,
                'verification_token': verification_token,
                'dayflow_role': role if role in ('employee', 'hr') else 'employee',
            }
            new_user = env['res.users'].sudo().create(user_vals)

            # Assign group
            if role == 'hr':
                hr_group = env.ref('backend.group_dayflow_hr', raise_if_not_found=False) or env.ref('dayflow.group_dayflow_hr', raise_if_not_found=False)
                if hr_group:
                    hr_group.sudo().write({'users': [(4, new_user.id)]})
            else:
                emp_group = env.ref('backend.group_dayflow_employee', raise_if_not_found=False) or env.ref('dayflow.group_dayflow_employee', raise_if_not_found=False)
                if emp_group:
                    emp_group.sudo().write({'users': [(4, new_user.id)]})

            # Create Dayflow Employee Profile
            emp_vals = {
                'name': name,
                'employee_code': employee_code,
                'user_id': new_user.id,
                'work_email': email,
                'phone': phone,
                'job_title': job_title,
                'department_name': department,
            }
            new_employee = env['dayflow.employee'].sudo().create(emp_vals)
            new_user.sudo().write({'dayflow_employee_id': new_employee.id})

            # Initialize base payroll record
            env['dayflow.payroll'].sudo().create({
                'employee_id': new_employee.id,
                'basic_salary': 50000.0,
                'hra': 15000.0,
                'special_allowance': 5000.0,
                'deductions': 2000.0,
            })

            return json_response(
                data={
                    'user_id': new_user.id,
                    'employee_id': new_employee.id,
                    'email': email,
                    'employee_code': employee_code,
                    'verification_token': verification_token,
                },
                message='Registration successful. Please verify your email to activate your account.',
                status=201
            )

        except Exception as e:
            _logger.exception("Signup error for %s: %s", email, str(e))
            return json_response(success=False, status=500, message=f"Registration failed: {str(e)}")

    @http.route('/api/auth/verify-email', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def verify_email(self, **kwargs):
        """Verify user account with token."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        body = get_json_body()
        email = (body.get('email') or '').strip().lower()
        token = (body.get('token') or '').strip()

        if not email or not token:
            return json_response(success=False, status=400, message='Email and verification token are required.')

        env = request.env(user=1)
        user = env['res.users'].sudo().search([('login', '=', email)], limit=1)

        if not user:
            return json_response(success=False, status=404, message='User account not found.')

        if user.is_verified:
            return json_response(success=True, message='Account is already verified. You may proceed to log in.')

        if user.verification_token == token:
            user.sudo().write({
                'is_verified': True,
                'verification_token': False,
            })
            return json_response(success=True, message='Email successfully verified! You can now log in.')
        else:
            return json_response(success=False, status=400, message='Invalid or expired verification token.')

    @http.route('/api/auth/me', type='http', auth='user', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def current_user(self, **kwargs):
        """Retrieve current logged in user session information."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        user = request.env.user
        employee = user.dayflow_employee_id or request.env['dayflow.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        role = 'hr' if is_hr_user(user) else 'employee'

        return json_response(data={
            'user_id': user.id,
            'employee_id': employee.id if employee else None,
            'name': employee.name if employee else user.name,
            'email': user.login,
            'role': role,
            'employee_code': employee.employee_code if employee else None,
            'is_verified': user.is_verified,
        })

    @http.route('/api/auth/logout', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def logout(self, **kwargs):
        """Log out current user and destroy session."""
        if request.httprequest.method == 'OPTIONS':
            return options_response()

        request.session.logout()
        return json_response(message='Logged out successfully.')
