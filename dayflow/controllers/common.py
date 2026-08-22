# -*- coding: utf-8 -*-
import json
import logging
from odoo.http import Response, request

_logger = logging.getLogger(__name__)

def get_cors_headers():
    """Dynamically determine CORS headers based on request origin to support credentials."""
    origin = '*'
    try:
        if hasattr(request, 'httprequest') and request.httprequest.headers.get('Origin'):
            origin = request.httprequest.headers.get('Origin')
    except Exception:
        origin = '*'

    headers = [
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', origin),
        ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, X-Dayflow-Token'),
    ]
    if origin != '*':
        headers.append(('Access-Control-Allow-Credentials', 'true'))

    return headers


def json_response(data=None, message=None, success=True, status=200, error=None):
    """Build standard JSON response with CORS headers."""
    payload = {
        'success': success,
        'status': status,
        'message': message or ('Success' if success else 'Error occurred'),
    }
    if data is not None:
        payload['data'] = data
    if error is not None:
        payload['error'] = error

    return Response(
        json.dumps(payload, default=str),
        status=status,
        headers=get_cors_headers()
    )


def options_response():
    """Return preflight response for OPTIONS requests."""
    return Response(status=204, headers=get_cors_headers())


def get_json_body():
    """Safely extract JSON body from request."""
    try:
        if hasattr(request, 'httprequest') and request.httprequest.data:
            return json.loads(request.httprequest.data.decode('utf-8'))
        return {}
    except Exception as e:
        _logger.warning("Failed to parse request JSON: %s", str(e))
        return {}


def is_hr_user(user):
    """Check if the user has HR Officer or Administrator privileges."""
    if not user:
        return False
    if getattr(user, '_is_admin', None) and user._is_admin():
        return True
    if getattr(user, 'id', None) == 1 or getattr(user, 'login', None) == 'admin':
        return True
    if getattr(user, 'dayflow_role', None) == 'hr':
        return True
    return (
        user.has_group('dayflow.group_dayflow_hr') or
        user.has_group('base.group_system')
    )


def get_auth_context():
    """
    Validate current user session and retrieve (user, employee, error_response).
    Returns (user, employee, None) on success, or (None, None, error_response) on failure.
    """
    uid = getattr(request.session, 'uid', None)
    if not uid and hasattr(request, 'env') and request.env.user and request.env.user.id:
        public_user = request.env.ref('base.public_user', raise_if_not_found=False)
        public_uid = public_user.id if public_user else None
        if request.env.user.id != public_uid:
            uid = request.env.user.id

    if not uid:
        return None, None, json_response(
            success=False,
            status=401,
            message='Authentication required. Please log in.'
        )

    user = request.env['res.users'].sudo().browse(uid)
    if not user.exists():
        return None, None, json_response(
            success=False,
            status=401,
            message='Session invalid or user does not exist.'
        )

    employee = user.dayflow_employee_id or request.env['dayflow.employee'].sudo().search(
        [('user_id', '=', user.id)], limit=1
    )
    return user, employee, None

