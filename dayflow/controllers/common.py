# -*- coding: utf-8 -*-
import json
import logging
from odoo.http import Response, request

_logger = logging.getLogger(__name__)

CORS_HEADERS = [
    ('Content-Type', 'application/json'),
    ('Access-Control-Allow-Origin', '*'),
    ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
    ('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, X-Dayflow-Token'),
    ('Access-Control-Allow-Credentials', 'true'),
]


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
        headers=CORS_HEADERS
    )


def options_response():
    """Return preflight response for OPTIONS requests."""
    return Response(status=204, headers=CORS_HEADERS)


def get_json_body():
    """Safely extract JSON body from request."""
    try:
        if request.httprequest.data:
            return json.loads(request.httprequest.data.decode('utf-8'))
        return {}
    except Exception as e:
        _logger.warning("Failed to parse request JSON: %s", str(e))
        return {}
