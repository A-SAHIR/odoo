# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PaieSlipLine(models.Model):
    _name = 'paie.slip.line'
    _description = 'Payslip Line'
    _order = 'sequence, id'

    slip_id = fields.Many2one(
        'paie.slip',
        string='Payslip',
        required=True,
        ondelete='cascade',
    )
    rule_id = fields.Many2one(
        'paie.rule',
        string='Salary Rule',
        required=True,
        ondelete='restrict',
    )
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    total = fields.Float(string='Total', digits='Payroll')
