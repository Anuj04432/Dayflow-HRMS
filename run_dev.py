# -*- coding: utf-8 -*-
"""
Dayflow HRMS - 1-Command Full-Stack Development Runner
=====================================================
Launches both the Backend API Server (Port 8069) and the Frontend Web Server (Port 8000)
concurrently in a single process with instant live testing URLs.

Usage:
    python run_dev.py
"""

import sys
import os
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from test_backend import DayflowMockHandler

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


class FrontendHandler(SimpleHTTPRequestHandler):
    """Custom static file server for Dayflow frontend assets."""
    def log_message(self, format, *args):
        # Quiet frontend asset requests
        pass


def run_full_stack():
    backend_port = 8069
    frontend_port = 8000

    backend_server = HTTPServer(('0.0.0.0', backend_port), DayflowMockHandler)
    frontend_server = HTTPServer(('0.0.0.0', frontend_port), FrontendHandler)

    backend_thread = threading.Thread(target=backend_server.serve_forever, daemon=True)
    frontend_thread = threading.Thread(target=frontend_server.serve_forever, daemon=True)

    backend_thread.start()
    frontend_thread.start()

    print("\n" + "="*75)
    print(" >>> DAYFLOW HRMS - FULL-STACK DEV SERVERS STARTED SUCCESSFULLY! <<<")
    print("="*75)
    print(f" [Backend API Server]  : http://localhost:{backend_port}")
    print(f" [Frontend Web Server] : http://localhost:{frontend_port}")
    print("="*75)
    print(" 🚀 READY-TO-USE APPLICATION LINKS:")
    print(f"    • Login Page           : http://localhost:{frontend_port}/frontend/index.html")
    print(f"    • Signup Page          : http://localhost:{frontend_port}/frontend/signup.html")
    print(f"    • Verify Email Page    : http://localhost:{frontend_port}/frontend/verify-email.html")
    print(f"    • Employee Dashboard   : http://localhost:{frontend_port}/frontend/employee-dashboard.html")
    print(f"    • HR Officer Dashboard : http://localhost:{frontend_port}/frontend/hr-dashboard.html")
    print("="*75)
    print(" 💡 PRE-CONFIGURED DEMO CREDENTIALS:")
    print("    👑 HR Admin : hr@dayflow.com       | password: password123")
    print("    👤 Employee : employee@dayflow.com | password: password123")
    print("="*75)
    print(" [INFO] Press Ctrl+C to stop both servers.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down Dayflow dev servers... Done.")
        backend_server.shutdown()
        frontend_server.shutdown()


if __name__ == '__main__':
    run_full_stack()
