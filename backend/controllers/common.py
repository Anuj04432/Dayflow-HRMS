# -*- coding: utf-8 -*-
import json
import logging
from odoo.http import Response, request

_logger = logging.getLogger(__name__)


def get_cors_headers():
    """Dynamically read incoming Origin to avoid browser credential CORS conflicts."""
    origin = '*'
    if hasattr(request, 'httprequest') and request.httprequest:
        origin = request.httprequest.headers.get('Origin') or '*'
    return [
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', origin),
        ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, X-Dayflow-Token'),
        ('Access-Control-Allow-Credentials', 'true'),
    ]


def is_hr_user(user):
    """Reliably determine if a user has HR/Admin privileges across different module installs."""
    if not user or (hasattr(user, '_is_public') and user._is_public()):
        return False
    if user.id == 1 or user.login == 'admin':
        return True
    if getattr(user, 'dayflow_role', False) == 'hr':
        return True
    return (
        user.has_group('backend.group_dayflow_hr') or
        user.has_group('dayflow.group_dayflow_hr') or
        user.has_group('dayflow_hrms.group_dayflow_hr')
    )


def json_response(data=None, message=None, success=True, status=200, error=None):
    """Build standard JSON response with dynamic CORS headers."""
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
    """Return preflight response for OPTIONS requests with dynamic CORS headers."""
    return Response(status=204, headers=get_cors_headers())


def get_json_body():
    """Safely extract JSON body from request."""
    try:
        if hasattr(request, 'httprequest') and request.httprequest and request.httprequest.data:
            return json.loads(request.httprequest.data.decode('utf-8'))
        return {}
    except Exception as e:
        _logger.warning("Failed to parse request JSON: %s", str(e))
        return {}
