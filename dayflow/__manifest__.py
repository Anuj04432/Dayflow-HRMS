# -*- coding: utf-8 -*-
{
    'name': 'Dayflow HRMS',
    'version': '1.0.0',
    'category': 'Human Resources',
    'summary': 'Every workday, perfectly aligned — Human Resource Management System',
    'description': """
Dayflow HRMS
=============
Core Odoo HRMS module managing:
- Authentication & Role-Based Access Control (Employee vs HR Officer)
- Employee Profiles & Permitted Field Edits
- Attendance Tracking (Daily/Weekly Check-in/Check-out)
- Leave & Time-off Management with HR Approval Workflows
- Salary Structure & Payroll Visibility
- REST / JSON Web APIs for Frontend Dashboard Integration
    """,
    'author': 'Dayflow Team',
    'website': 'https://github.com/Anuj04432/Dayflow-HRMS',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
