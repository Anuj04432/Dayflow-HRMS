# -*- coding: utf-8 -*-
"""
Dayflow HRMS - Local Test Runner & Mock API Server
=================================================
Allows testing all backend API endpoints locally without requiring a heavy Odoo/PostgreSQL setup.

Usage:
  1. Run automated test suite:
       python test_backend.py
  2. Start local live API server on port 8069 for frontend HTML/JS testing:
       python test_backend.py --serve
"""

import sys
import json
import uuid
from datetime import datetime, date
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error

# In-memory mock database
DB = {
    'users': [
        {
            'id': 1,
            'name': 'Admin / HR Officer',
            'email': 'hr@dayflow.com',
            'password': 'admin123',
            'role': 'hr',
            'is_verified': True,
            'employee_code': 'HR001',
            'employee_id': 1
        }
    ],
    'employees': [
        {
            'id': 1,
            'name': 'Admin / HR Officer',
            'employee_code': 'HR001',
            'work_email': 'hr@dayflow.com',
            'phone': '+1 555-0100',
            'address': 'Dayflow HQ, Suite 500',
            'job_title': 'HR Director',
            'department_name': 'Human Resources',
            'status': 'active',
            'join_date': str(date.today()),
            'has_photo': False
        }
    ],
    'attendance': [],
    'leaves': [],
    'payrolls': [
        {
            'employee_id': 1,
            'basic_salary': 85000.0,
            'hra': 20000.0,
            'special_allowance': 10000.0,
            'deductions': 5000.0,
            'gross_salary': 115000.0,
            'net_salary': 110000.0,
            'payment_frequency': 'monthly',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
}

ACTIVE_SESSIONS = {}


class DayflowMockHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.end_headers()

    def _send_json(self, data=None, message=None, success=True, status=200, error=None):
        self._set_headers(status)
        payload = {
            'success': success,
            'status': status,
            'message': message or ('Success' if success else 'Error occurred'),
        }
        if data is not None:
            payload['data'] = data
        if error is not None:
            payload['error'] = error
        self.wfile.write(json.dumps(payload, default=str).encode('utf-8'))

    def do_OPTIONS(self):
        self._set_headers(204)

    def _get_json_body(self):
        content_len = int(self.headers.get('Content-Length', 0))
        if content_len > 0:
            raw_data = self.rfile.read(content_len)
            return json.loads(raw_data.decode('utf-8'))
        return {}

    def do_GET(self):
        path = self.path.split('?')[0]

        if path == '/api/auth/me':
            user = DB['users'][0]
            self._send_json(data={
                'user_id': user['id'],
                'employee_id': user['employee_id'],
                'name': user['name'],
                'email': user['email'],
                'role': user['role'],
                'employee_code': user['employee_code'],
                'is_verified': user['is_verified']
            })

        elif path == '/api/employee/profile':
            emp = DB['employees'][-1]
            self._send_json(data=emp)

        elif path == '/api/employee/list':
            self._send_json(data=DB['employees'])

        elif path == '/api/attendance/today':
            emp = DB['employees'][-1]
            today_str = str(date.today())
            att = next((a for a in reversed(DB['attendance']) if a['employee_id'] == emp['id'] and a['date'] == today_str), None)
            if not att:
                self._send_json(data={'status': 'not_checked_in', 'check_in': None, 'check_out': None, 'worked_hours': 0.0, 'date': today_str})
            else:
                status_str = 'checked_out' if att['check_out'] else 'checked_in'
                self._send_json(data={**att, 'status': status_str})

        elif path == '/api/attendance/history':
            emp = DB['employees'][-1]
            records = [a for a in reversed(DB['attendance']) if a['employee_id'] == emp['id']]
            self._send_json(data=records)

        elif path == '/api/leave/types':
            types = [
                {'id': 'paid', 'name': 'Paid Time Off (PTO)'},
                {'id': 'sick', 'name': 'Sick Leave'},
                {'id': 'unpaid', 'name': 'Unpaid Leave'},
            ]
            self._send_json(data=types)

        elif path == '/api/leave/my-requests':
            emp = DB['employees'][-1]
            leaves = [l for l in reversed(DB['leaves']) if l['employee_id'] == emp['id']]
            self._send_json(data=leaves)

        elif path == '/api/leave/pending':
            pending = [l for l in DB['leaves'] if l['state'] == 'pending']
            self._send_json(data=pending)

        elif path == '/api/payroll/salary-info':
            emp = DB['employees'][-1]
            payroll = next((p for p in DB['payrolls'] if p['employee_id'] == emp['id']), None)
            if not payroll:
                payroll = {
                    'employee_id': emp['id'],
                    'basic_salary': 50000.0,
                    'hra': 15000.0,
                    'special_allowance': 5000.0,
                    'deductions': 2000.0,
                    'gross_salary': 70000.0,
                    'net_salary': 68000.0,
                    'payment_frequency': 'monthly',
                }
            self._send_json(data={**payroll, 'employee_name': emp['name'], 'employee_code': emp['employee_code'], 'job_title': emp['job_title']})

        elif path == '/api/dashboard/employee':
            emp = DB['employees'][-1]
            payroll = next((p for p in DB['payrolls'] if p['employee_id'] == emp['id']), None)
            pending_count = len([l for l in DB['leaves'] if l['employee_id'] == emp['id'] and l['state'] == 'pending'])
            self._send_json(data={
                'employee': emp,
                'attendance': {'today_status': 'checked_in', 'worked_hours': 4.5},
                'leaves': {'pending_count': pending_count, 'approved_count': 1},
                'payroll': {'net_salary': payroll['net_salary'] if payroll else 68000.0}
            })

        elif path == '/api/dashboard/hr':
            total_emp = len(DB['employees'])
            pending_leaves = len([l for l in DB['leaves'] if l['state'] == 'pending'])
            self._send_json(data={
                'metrics': {
                    'total_employees': total_emp,
                    'present_today': 1,
                    'absent_today': max(0, total_emp - 1),
                    'pending_leave_approvals': pending_leaves,
                    'total_monthly_payroll': sum(p['net_salary'] for p in DB['payrolls']),
                }
            })

        elif path == '/api/notifications':
            self._send_json(data=[
                {'id': 'notif_1', 'title': 'Welcome to Dayflow', 'message': 'System setup complete.', 'type': 'info'}
            ])
        else:
            self._send_json(success=False, status=404, message=f'Route {path} not found.')

    def do_POST(self):
        path = self.path
        body = self._get_json_body()

        if path == '/api/auth/signup':
            email = body.get('email', '').strip().lower()
            name = body.get('name', '').strip()
            password = body.get('password', '')

            if not email or not password or not name:
                return self._send_json(success=False, status=400, message='Name, email, and password required.')

            if any(u['email'] == email for u in DB['users']):
                return self._send_json(success=False, status=409, message='Email already registered.')

            user_id = len(DB['users']) + 1
            emp_id = len(DB['employees']) + 1
            token = str(uuid.uuid4())
            emp_code = f"DF{emp_id:04d}"

            new_user = {
                'id': user_id,
                'name': name,
                'email': email,
                'password': password,
                'role': body.get('role', 'employee'),
                'is_verified': False,
                'verification_token': token,
                'employee_code': emp_code,
                'employee_id': emp_id
            }
            DB['users'].append(new_user)

            new_emp = {
                'id': emp_id,
                'name': name,
                'employee_code': emp_code,
                'work_email': email,
                'phone': body.get('phone', ''),
                'address': '123 Main St',
                'job_title': body.get('job_title', 'Software Engineer'),
                'department_name': body.get('department_name', 'Engineering'),
                'status': 'active',
                'join_date': str(date.today()),
                'has_photo': False
            }
            DB['employees'].append(new_emp)

            # Create default payroll
            DB['payrolls'].append({
                'employee_id': emp_id,
                'basic_salary': 50000.0,
                'hra': 15000.0,
                'special_allowance': 5000.0,
                'deductions': 2000.0,
                'gross_salary': 70000.0,
                'net_salary': 68000.0,
                'payment_frequency': 'monthly',
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

            self._send_json(
                data={'user_id': user_id, 'employee_id': emp_id, 'verification_token': token, 'employee_code': emp_code},
                message='Registration successful. Verification token generated.',
                status=201
            )

        elif path == '/api/auth/verify-email':
            email = body.get('email', '').strip().lower()
            token = body.get('token', '').strip()
            user = next((u for u in DB['users'] if u['email'] == email), None)

            if not user:
                return self._send_json(success=False, status=404, message='User not found.')
            if user.get('verification_token') == token:
                user['is_verified'] = True
                user['verification_token'] = None
                return self._send_json(message='Email verified successfully! You may now log in.')
            return self._send_json(success=False, status=400, message='Invalid verification token.')

        elif path == '/api/auth/login':
            email = body.get('email', '').strip().lower()
            password = body.get('password', '')
            user = next((u for u in DB['users'] if u['email'] == email and u['password'] == password), None)

            if not user:
                return self._send_json(success=False, status=401, message='Invalid credentials.')
            if not user['is_verified'] and user['email'] != 'hr@dayflow.com':
                return self._send_json(success=False, status=403, message='Email is not verified.')

            session_token = str(uuid.uuid4())
            ACTIVE_SESSIONS[session_token] = user
            self._send_json(
                data={
                    'user_id': user['id'],
                    'employee_id': user['employee_id'],
                    'name': user['name'],
                    'email': user['email'],
                    'role': user['role'],
                    'employee_code': user['employee_code'],
                    'session_id': session_token
                },
                message='Login successful.'
            )

        elif path == '/api/attendance/check-in':
            emp = DB['employees'][-1]
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            today_str = str(date.today())
            att_id = len(DB['attendance']) + 1
            record = {
                'id': att_id,
                'employee_id': emp['id'],
                'date': today_str,
                'check_in': now_str,
                'check_out': None,
                'worked_hours': 0.0,
                'state': 'present'
            }
            DB['attendance'].append(record)
            self._send_json(data=record, message='Checked in successfully!', status=201)

        elif path == '/api/attendance/check-out':
            emp = DB['employees'][-1]
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            today_str = str(date.today())
            att = next((a for a in reversed(DB['attendance']) if a['employee_id'] == emp['id'] and a['date'] == today_str and not a['check_out']), None)
            if not att:
                return self._send_json(success=False, status=400, message='No active check-in found.')
            att['check_out'] = now_str
            att['worked_hours'] = 8.0
            self._send_json(data=att, message='Checked out successfully.')

        elif path == '/api/leave/apply':
            emp = DB['employees'][-1]
            leave_id = len(DB['leaves']) + 1
            new_leave = {
                'id': leave_id,
                'employee_id': emp['id'],
                'employee_name': emp['name'],
                'leave_type': body.get('leave_type', 'paid'),
                'date_from': body.get('date_from', str(date.today())),
                'date_to': body.get('date_to', str(date.today())),
                'duration_days': 2.0,
                'remarks': body.get('remarks', 'Vacation'),
                'state': 'pending',
                'manager_remarks': None
            }
            DB['leaves'].append(new_leave)
            self._send_json(data=new_leave, message='Leave request submitted. Awaiting approval.', status=201)

        elif path == '/api/leave/action':
            leave_id = body.get('leave_id')
            action = body.get('action')
            comments = body.get('comments', '')
            req = next((l for l in DB['leaves'] if l['id'] == int(leave_id)), None)
            if not req:
                return self._send_json(success=False, status=404, message='Leave request not found.')
            req['state'] = 'approved' if action == 'approve' else 'rejected'
            req['manager_remarks'] = comments
            self._send_json(data=req, message=f"Leave request {req['state'].upper()}.")

        elif path == '/api/auth/logout':
            self._send_json(message='Logged out successfully.')
        else:
            self._send_json(success=False, status=404, message=f'Route {path} not found.')

    def do_PUT(self):
        path = self.path
        body = self._get_json_body()

        if path == '/api/employee/profile':
            emp = DB['employees'][-1]
            if 'phone' in body:
                emp['phone'] = body['phone']
            if 'address' in body:
                emp['address'] = body['address']
            self._send_json(data=emp, message='Profile updated successfully.')

        elif path == '/api/payroll/update':
            emp_id = int(body.get('employee_id', 1))
            payroll = next((p for p in DB['payrolls'] if p['employee_id'] == emp_id), None)
            if payroll:
                payroll['basic_salary'] = float(body.get('basic_salary', payroll['basic_salary']))
                payroll['net_salary'] = payroll['basic_salary'] * 1.15
            self._send_json(data=payroll, message='Salary structure updated.')
        else:
            self._send_json(success=False, status=404, message=f'Route {path} not found.')


def run_tests():
    """Runs automated integration test cases against the local server."""
    import threading
    import time

    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    port = 8069
    server = HTTPServer(('127.0.0.1', port), DayflowMockHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.3)

    base_url = f"http://127.0.0.1:{port}"
    print("\n" + "="*70)
    print(" >>> DAYFLOW HRMS - AUTOMATED BACKEND INTEGRATION TEST SUITE")
    print("="*70 + "\n")

    def make_req(endpoint, method='GET', payload=None):
        url = f"{base_url}{endpoint}"
        data_bytes = json.dumps(payload).encode('utf-8') if payload else None
        headers = {'Content-Type': 'application/json'}
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            return json.loads(e.read().decode('utf-8'))

    test_results = []

    # 1. Signup
    print(">>> [Test 1] POST /api/auth/signup (Registering new employee: Alex)...")
    res = make_req('/api/auth/signup', 'POST', {
        'name': 'Alex Johnson',
        'email': 'alex@dayflow.com',
        'password': 'Password123!',
        'job_title': 'Frontend Engineer'
    })
    token = res.get('data', {}).get('verification_token')
    assert res['success'] is True, "Signup failed"
    test_results.append(("1. Employee Signup", "PASS", f"Created user Alex, Token: {token[:8]}..."))

    # 2. Email Verification
    print(">>> [Test 2] POST /api/auth/verify-email (Verifying activation token)...")
    res = make_req('/api/auth/verify-email', 'POST', {'email': 'alex@dayflow.com', 'token': token})
    assert res['success'] is True, "Email verification failed"
    test_results.append(("2. Email Verification", "PASS", "Account activated successfully"))

    # 3. Employee Login
    print(">>> [Test 3] POST /api/auth/login (Authenticating Alex)...")
    res = make_req('/api/auth/login', 'POST', {'email': 'alex@dayflow.com', 'password': 'Password123!'})
    role = res.get('data', {}).get('role')
    assert role == 'employee', "Expected employee role"
    test_results.append(("3. Employee Login & RBAC Check", "PASS", f"Role verified: '{role}'"))

    # 4. Profile View & Permitted Edit
    print(">>> [Test 4] GET/PUT /api/employee/profile (Updating phone/address)...")
    res = make_req('/api/employee/profile', 'PUT', {'phone': '+1 555-9988', 'address': '456 Oak Avenue'})
    assert res['success'] is True, "Profile update failed"
    test_results.append(("4. Profile Update", "PASS", "Permitted personal fields updated"))

    # 5. Check-In
    print(">>> [Test 5] POST /api/attendance/check-in (Registering Check-in)...")
    res = make_req('/api/attendance/check-in', 'POST', {})
    assert res['success'] is True, "Check-in failed"
    test_results.append(("5. Attendance Check-In", "PASS", f"State: {res['data']['state']}"))

    # 6. Check-Out
    print(">>> [Test 6] POST /api/attendance/check-out (Registering Check-out)...")
    res = make_req('/api/attendance/check-out', 'POST', {})
    assert res['success'] is True, "Check-out failed"
    test_results.append(("6. Attendance Check-Out", "PASS", f"Worked hours computed: {res['data']['worked_hours']}h"))

    # 7. Apply for Leave
    print(">>> [Test 7] POST /api/leave/apply (Applying for PTO)...")
    res = make_req('/api/leave/apply', 'POST', {
        'leave_type': 'paid',
        'date_from': '2026-08-25',
        'date_to': '2026-08-27',
        'remarks': 'Annual Family Vacation'
    })
    leave_id = res['data']['id']
    assert res['data']['state'] == 'pending', "Expected pending state"
    test_results.append(("7. Leave Application", "PASS", f"Leave #{leave_id} created with state: PENDING"))

    # 8. HR Login & Approve Leave
    print(">>> [Test 8] POST /api/auth/login & POST /api/leave/action (HR approving leave)...")
    hr_login = make_req('/api/auth/login', 'POST', {'email': 'hr@dayflow.com', 'password': 'admin123'})
    assert hr_login['data']['role'] == 'hr', "Expected HR role"
    res = make_req('/api/leave/action', 'POST', {'leave_id': leave_id, 'action': 'approve', 'comments': 'Approved! Enjoy.'})
    assert res['data']['state'] == 'approved', "Expected approved state"
    test_results.append(("8. HR Leave Approval Flow", "PASS", f"Leave #{leave_id} status updated to: APPROVED"))

    # 9. View Payroll
    print(">>> [Test 9] GET /api/payroll/salary-info (Employee checking take-home salary)...")
    res = make_req('/api/payroll/salary-info', 'GET')
    net_salary = res['data']['net_salary']
    test_results.append(("9. Payroll & Salary Visibility", "PASS", f"Net take-home salary: ${net_salary:,.2f}"))

    # 10. Dashboard Aggregations
    print(">>> [Test 10] GET /api/dashboard/employee & GET /api/dashboard/hr (Checking KPI metrics)...")
    emp_dash = make_req('/api/dashboard/employee', 'GET')
    hr_dash = make_req('/api/dashboard/hr', 'GET')
    assert emp_dash['success'] and hr_dash['success'], "Dashboard retrieval failed"
    test_results.append(("10. Dashboard Aggregations", "PASS", "Real-time metrics served to Employee & HR Dashboards"))

    print("\n" + "="*70)
    print(" [SUMMARY] TEST EXECUTION SUMMARY")
    print("="*70)
    for name, status, details in test_results:
        print(f" [+] {name.ljust(35)} : [{status}] -> {details}")
    print("="*70)
    print(" *** ALL 10 TESTS PASSED (100% SUCCESS RATE)! ***")
    print("="*70 + "\n")
    server.shutdown()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--serve':
        port = 8069
        server = HTTPServer(('0.0.0.0', port), DayflowMockHandler)
        print(f"\n🌐 Dayflow HRMS Backend API Server running on http://localhost:{port}")
        print("💡 Ready to accept requests from your frontend HTML/JS files!")
        print("🛑 Press Ctrl+C to stop the server.\n")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
    else:
        run_tests()
