# -*- coding: utf-8 -*-
import uuid
from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    dayflow_employee_id = fields.Many2one(
        'dayflow.employee',
        string='Dayflow Employee Profile',
        ondelete='set null'
    )
    is_verified = fields.Boolean(
        string='Email Verified',
        default=False,
        help='Indicates if the user has verified their email address'
    )
    verification_token = fields.Char(
        string='Verification Token',
        copy=False,
        help='Token used for email verification'
    )
    dayflow_role = fields.Selection(
        [('employee', 'Employee'), ('hr', 'HR Officer / Admin')],
        string='Dayflow Role',
        default='employee',
        required=True
    )

    def generate_verification_token(self):
        """Generate a unique verification token for email activation."""
        for user in self:
            user.verification_token = str(uuid.uuid4())
        return True

    def verify_account(self, token):
        """Verify the user account if token matches."""
        self.ensure_one()
        if self.verification_token and self.verification_token == token:
            self.write({
                'is_verified': True,
                'verification_token': False,
            })
            return True
        return False
