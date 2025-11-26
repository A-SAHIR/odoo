# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'La Paie Maroc (Community)',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Moroccan Payroll Management for Odoo Community Edition',
    'description': """
Moroccan Payroll Management
===========================
This module provides payroll management for Morocco (Community Edition).

Features:
- Configurable salary rules
- Payslip generation with automatic computation
- Default Moroccan rules (CNSS, AMO, etc.)
    """,
    'depends': ['base', 'hr', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/paie_rule_views.xml',
        'views/paie_slip_views.xml',
        'views/paie_menu.xml',
        'data/paie_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
