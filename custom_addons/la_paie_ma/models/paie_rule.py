# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PaieRule(models.Model):
    _name = 'paie.rule'
    _description = 'Salary Rule'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(
        string='Code',
        required=True,
        help='Unique code for this rule, used in computations',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Defines the order in which rules are computed',
    )
    category = fields.Selection(
        selection=[
            ('basic', 'Basic'),
            ('gross', 'Gross'),
            ('deduction', 'Deduction'),
            ('net', 'Net'),
        ],
        string='Category',
        required=True,
        default='basic',
    )
    python_code = fields.Text(
        string='Python Code',
        default='result = 0',
        help="""Python code to compute the rule amount.
Available variables:
- contract: the employee contract with wage
- categories: dictionary of category totals (BASIC, GROSS, DEDUCTION, NET)
- payslip: the current payslip
- employee: the employee

The code must set the 'result' variable.
Example: result = contract.wage * 0.10
""",
    )
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The rule code must be unique!'),
    ]

    @api.constrains('code')
    def _check_code(self):
        for rule in self:
            if rule.code and not rule.code.isidentifier():
                raise ValidationError(_("The code '%s' is not a valid Python identifier.", rule.code))
